import yaml
import gzip
import orjson as json

from joblib import Parallel, delayed

sitelinks = {
    'itwiki': 'https://it.wikipedia.org/wiki/',
    'enwiki': 'https://en.wikipedia.org/wiki/'
}

with open('recipe_examples/instances_it.yaml', 'rt') as fp_yaml:
    recipe = yaml.load(fp_yaml, Loader=yaml.BaseLoader)


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


def resolve_rule(field, rule, value):
    if field == "sitelinks":
        return '<' + sitelinks[rule] + value.replace(' ', '_') + '>'
    else:
        return '"' + value + '"@' + rule


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
                    raise ValueError()
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
                raise ValueError()


def process_line(line):
    if line[0] == '[' or line[0] == ']':
        return

    line = line.strip()

    if line[-1] == ',':
        line = line[:-1]

    entity = json.loads(line)

    result = []

    try:
        run_recipe(entity, result, 'labels')
        run_recipe(entity, result, 'descriptions')
        run_recipe(entity, result, 'aliases')
        run_recipe(entity, result, 'sitelinks')
        run_recipe(entity, result, 'claims')
        run_recipe(entity, result, 'filters')
    except ValueError:
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


with gzip.open('100k.json.gz', 'rt') as fp_json:
    triples = Parallel(n_jobs=2, verbose=50)(delayed(process_line)(raw_line) for raw_line in fp_json)

    with open('result.ttl', 'w') as fp_out:
        fp_out.write("""@prefix wd: <http://www.wikidata.org/entity/> .
@prefix wdt: <http://www.wikidata.org/prop/direct/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
""")
        for triple in triples:
            if triple is not None:
                fp_out.write(triple + '\n')
