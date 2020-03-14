import argparse
import gzip
import orjson
import yaml

from joblib import Parallel, delayed

# TODO create lookup file
sitelinks = {
    'itwiki': 'https://it.wikipedia.org/wiki/',
    'enwiki': 'https://en.wikipedia.org/wiki/'
}


def resolve_rule(field, rule, value):
    if field == "sitelinks":
        return '<' + sitelinks[rule] + value.replace(' ', '_') + '>'
    else:
        return '"' + value + '"@' + rule


def resolve_snak(snak):
    datatype = snak['mainsnak']['datatype']
    value = snak['mainsnak']['datavalue']['value']

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

    if field not in recipe:
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

    result = []

    try:
        run_recipe(entity, result, 'labels')
        run_recipe(entity, result, 'descriptions')
        run_recipe(entity, result, 'aliases')
        run_recipe(entity, result, 'sitelinks')
        run_recipe(entity, result, 'claims')
        run_recipe(entity, result, 'filters')
    except UserWarning:
        return

    for triple in result:
        subject = 'wd:' + triple[0]

        if triple[1] == "labels":
            predicate = "schema:name"
        elif triple[1] == "descriptions":
            predicate = "schema:description"
        elif triple[1] == "aliases":
            predicate = "skos:altLabel"
        elif triple[1] == "sitelinks":
            predicate = "schema:about"
        else:
            predicate = "wdt:" + triple[1]

        if triple[2][0] == 'Q':
            obj = 'wd:' + triple[2]
        else:
            obj = triple[2]

        if triple[1] == 'sitelinks':
            line = obj + ' ' + predicate + ' ' + subject + ' .'
        else:
            line = subject + ' ' + predicate + ' ' + obj + ' .'

        return line


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Wikidata lite')
    parser.add_argument('recipe', help='The YAML recipe file')
    parser.add_argument('input', help='The gzipped Wikidata JSON dump')
    parser.add_argument('output', help='The TTL output file')
    parser.add_argument('--n_jobs', type=int, default=2, help='The number of workers')
    parser.add_argument('--verbose', type=int, default=50, help='The verbosity level')

    args = parser.parse_args()

    with open(args.recipe, 'rt') as fp_yaml:
        recipe = yaml.load(fp_yaml, Loader=yaml.BaseLoader)

    # TODO validate recipe

    with gzip.open(args.input, 'rt') as fp_in:
        triples = Parallel(n_jobs=args.n_jobs, verbose=args.verbose)(
            delayed(process_line)(raw_line) for raw_line in fp_in)

        with open(args.output, 'w') as fp_out:
            fp_out.write("@prefix wd: <http://www.wikidata.org/entity/> .\n")
            fp_out.write("@prefix wdt: <http://www.wikidata.org/prop/direct/> .\n")
            fp_out.write("@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .\n")
            fp_out.write("@prefix skos: <http://www.w3.org/2004/02/skos/core#> .\n")

            for triple in triples:
                if triple is not None:
                    fp_out.write(triple + '\n')
