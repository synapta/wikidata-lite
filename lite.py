import csv

import argparse
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


def resolve_rule(field, rule, value):
    if field == "sitelinks":
        return '<' + sitelinks[rule] + value.replace(' ', '_') + '>'
    else:
        return '"' + value + '"@' + rule


def resolve_snak(snak):
    datatype = snak['mainsnak']['datatype']
    try:
        value = snak['mainsnak']['datavalue']['value']
    except KeyError:
        raise NotImplementedError()

    if datatype == 'wikibase-item':
        result = value['id']
    elif datatype == 'external-id':
        result = '"' + value + '"'
    elif datatype == 'commonsMedia':
        result = value  # TODO
    elif datatype == 'string':
        result = '"' + value + '"'
    elif datatype == 'url':
        result = '"' + value + '"'
    elif datatype == 'quantity':
        result = value['amount'] + ' ' + value['unit']  # TODO
    elif datatype == 'time':
        result = value['time'] + ' ' + str(value['precision'])  # TODO
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
    parser = argparse.ArgumentParser(description='Wikidata lite')
    parser.add_argument('recipe', help='The YAML recipe file')
    parser.add_argument('input', help='The Wikidata JSON dump')
    parser.add_argument('output', help='The TTL output file')
    parser.add_argument('--n_jobs', type=int, default=2, help='The number of workers')
    parser.add_argument('--verbose', type=int, default=50, help='The verbosity level')

    args = parser.parse_args()

    load_sitelinks('sitelinks.csv')

    with open(args.recipe, 'rt') as fp_yaml:
        recipe = yaml.load(fp_yaml, Loader=yaml.BaseLoader)

    # TODO validate recipe

    with xopen(args.input, 'rt') as fp_in, xopen(args.output, 'w') as fp_out:
        fp_out.write("@prefix wd: <http://www.wikidata.org/entity/> .\n")
        fp_out.write("@prefix wdt: <http://www.wikidata.org/prop/direct/> .\n")
        fp_out.write("@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .\n")
        fp_out.write("@prefix skos: <http://www.w3.org/2004/02/skos/core#> .\n")

        for triples in Parallel(n_jobs=args.n_jobs, verbose=args.verbose)(
                delayed(process_line)(raw_line) for raw_line in fp_in):
            if triples is not None:
                [fp_out.write(triple + '\n') for triple in triples]
