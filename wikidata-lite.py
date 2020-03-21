import argparse
import csv
import sys

import orjson
import yaml
from joblib import Parallel, delayed
from xopen import xopen

sitelinks = {}


def load_sitelinks(file_name):
    global sitelinks

    with open(file_name) as fp:
        reader = csv.reader(fp, delimiter=',')
        for row in reader:
            if len(row) == 2:
                sitelinks[row[0]] = row[1]


def validate_recipe(recipe_dict):
    sections = ['labels', 'descriptions', 'aliases', 'sitelinks', 'claims', 'filters']

    for section in recipe_dict.keys():
        if section not in sections:
            print('Unknown section', section)
            raise ValueError

    if 'sitelinks' in recipe_dict:
        validate_sitelinks(recipe_dict['sitelinks'])

    for section_name in sections:
        if section_name in recipe_dict:
            validate_section(recipe_dict[section_name], section_name)


def validate_sitelinks(section):
    for rule in section:
        fields = rule.split(' ')

        if fields[0] not in sitelinks:
            print('Please add sitelink', fields[0], 'to sitelinks.csv')
            raise ValueError


def validate_section(section, section_name):
    for rule in section:
        fields = rule.split(' ')

        if len(fields) > 2:
            print('Too many values in rule', rule)
            raise ValueError
        elif len(fields) == 2 and fields[1] != 'optional' and section_name != 'filters':
            print('Value', fields[1], 'must be optional')
            raise ValueError
        elif section_name == 'filters' and len(fields) != 2:
            print('Filter', rule, 'must have two values')
            raise ValueError
        elif len(fields) < 1 or fields == ['']:
            print('Rule cannot be empty')
            raise ValueError


def resolve_rule(field, rule, value):
    if field == "sitelinks":
        return '<' + sitelinks[rule] + value.replace(' ', '_') + '>'
    else:
        return orjson.dumps(value).decode() + '@' + rule


def resolve_snak(snak):
    datatype = snak['mainsnak']['datatype']
    try:
        value = snak['mainsnak']['datavalue']['value']
    except KeyError:
        raise NotImplementedError()

    if datatype == 'wikibase-item':
        result = value['id']
    elif datatype == 'external-id':
        result = orjson.dumps(value).decode()
    elif datatype == 'commonsMedia':
        result = '<http://commons.wikimedia.org/wiki/Special:FilePath/' + value + '>'
    elif datatype == 'string':
        result = orjson.dumps(value).decode()
    elif datatype == 'url':
        result = orjson.dumps(value).decode()
    elif datatype == 'quantity':
        result = '"' + value['amount'] + '"^^xsd:decimal'
    elif datatype == 'time':
        result = '"' + value['time'] + '"^^xsd:dateTime'
    elif datatype == 'globe-coordinate':
        result = '"Point(' + str(value['longitude']) + ' ' + str(value['latitude']) + ')"^^geo:wktLiteral'
    else:
        raise NotImplementedError()

    return result


def run_recipe(entity, result, field):
    if field == 'sitelinks':
        value = 'title'
    else:
        value = 'value'

    if field not in recipe or field not in entity:
        return

    for r_label in recipe[field]:
        label = r_label.split()
        rule = label[0]

        if field == 'filters':
            if rule in entity['claims']:
                filtered = False
                for claim in entity['claims'][rule]:
                    if resolve_snak(claim) == label[1]:
                        filtered = True
                if filtered:
                    raise UserWarning()
        elif rule in entity[field]:
            if field == 'aliases':
                for alias in entity[field][rule]:
                    result.append((entity['id'], field, resolve_rule(field, rule, alias[value])))
            elif field == 'claims':
                for claim in entity[field][rule]:
                    try:
                        result.append((entity['id'], rule, resolve_snak(claim)))
                    except NotImplementedError:
                        pass
            else:
                result.append((entity['id'], field, resolve_rule(field, rule, entity[field][rule][value])))
        else:
            if len(label) == 1:
                raise UserWarning()


def process_line(line):
    if line[0] == '[' or line[0] == ']':
        return

    line = line.strip()

    if line[-1] == ',':
        line = line[:-1]

    entity = orjson.loads(line)

    accumulator = []

    try:
        run_recipe(entity, accumulator, 'labels')
        run_recipe(entity, accumulator, 'descriptions')
        run_recipe(entity, accumulator, 'aliases')
        run_recipe(entity, accumulator, 'sitelinks')
        run_recipe(entity, accumulator, 'claims')
        run_recipe(entity, accumulator, 'filters')
    except UserWarning:
        return

    lines_out = []

    for assertion in accumulator:
        subject = 'wd:' + assertion[0]

        if assertion[1] == "labels":
            predicate = "schema:name"
        elif assertion[1] == "descriptions":
            predicate = "schema:description"
        elif assertion[1] == "aliases":
            predicate = "skos:altLabel"
        elif assertion[1] == "sitelinks":
            predicate = "schema:about"
        else:
            predicate = "wdt:" + assertion[1]

        if assertion[2][0] == 'Q':
            obj = 'wd:' + assertion[2]
        else:
            obj = assertion[2]

        if assertion[1] == 'sitelinks':
            line_out = obj + ' ' + predicate + ' ' + subject + ' .'
        else:
            line_out = subject + ' ' + predicate + ' ' + obj + ' .'

        lines_out.append(line_out)

    return lines_out


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Wikidata-lite')
    parser.add_argument('recipe', help='The YAML recipe file')
    parser.add_argument('wikidata', help='The Wikidata JSON dump')
    parser.add_argument('rdf', help='The TTL output file')
    parser.add_argument('--n_jobs', type=int, default=2, help='The number of workers')
    parser.add_argument('--verbose', type=int, default=50, help='The verbosity level')

    args = parser.parse_args()

    load_sitelinks('sitelinks.csv')

    with open(args.recipe, 'rt') as fp_yaml:
        recipe = yaml.load(fp_yaml, Loader=yaml.BaseLoader)

    try:
        validate_recipe(recipe)
    except ValueError:
        sys.exit(1)

    with xopen(args.wikidata, 'rt') as fp_in, xopen(args.rdf, 'w') as fp_out:
        fp_out.write("@prefix wd: <http://www.wikidata.org/entity/> .\n")
        fp_out.write("@prefix wdt: <http://www.wikidata.org/prop/direct/> .\n")
        fp_out.write("@prefix schema: <http://schema.org/> .\n")
        fp_out.write("@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .\n")
        fp_out.write("@prefix skos: <http://www.w3.org/2004/02/skos/core#> .\n")
        fp_out.write("@prefix geo: <http://www.opengis.net/ont/geosparql#> .\n")

        for triples in Parallel(n_jobs=args.n_jobs, verbose=args.verbose)(
                delayed(process_line)(raw_line) for raw_line in fp_in):
            if triples is not None:
                [fp_out.write(triple + '\n') for triple in triples]
