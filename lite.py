import yaml
import gzip
import orjson as json

sitelinks = {
    'itwiki': 'https://it.wikipedia.org/wiki/',
    'enwiki': 'https://en.wikipedia.org/wiki/'
}

with open('recipe_examples/instances_it.yaml', 'rt') as fp_yaml:
    recipe = yaml.load(fp_yaml, Loader=yaml.BaseLoader)
    print(recipe)

counter = 0
found = 0
print("Wikidata entity found: %s/%s" % (found, counter))


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


def run_recipe(recipe, entity, result, field):
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


with gzip.open('1k.json.gz', 'rt') as fp_json:

    # @prefix wd: <http://www.wikidata.org/entity/> .
    # @prefix wdt: <http://www.wikidata.org/prop/direct/> .
    # @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
    # @prefix skos: <http://www.w3.org/2004/02/skos/core#> .

    for line in fp_json:

        if line[0] == '[' or line[0] == ']':
            continue

        line = line.strip()

        if line[-1] == ',':
            line = line[:-1]

        counter += 1

        if counter % 10000 == 0:
            print("Wikidata entity found: %s/%s" % (found, counter))

        entity = json.loads(line)

        result = []

        try:
            run_recipe(recipe, entity, result, 'labels')
            run_recipe(recipe, entity, result, 'descriptions')
            run_recipe(recipe, entity, result, 'aliases')
            run_recipe(recipe, entity, result, 'sitelinks')
            run_recipe(recipe, entity, result, 'claims')
            run_recipe(recipe, entity, result, 'filters')
        except ValueError:
            continue

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

            print(line)

        found += 1

print("Wikidata entity found: %s/%s" % (found, counter))
