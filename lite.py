import yaml
import gzip
import orjson as json

'''
{
    type: 'item',
    id: 'Q31',
    labels : [],
    descriptions: [],
    aliases: [],
    claims: [],
    sitelinks: [],
    lastrevid: 12345
}
'''

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
        result = value
    elif datatype == 'commonsMedia':
        result = value
    elif datatype == 'string':
        result = value
    elif datatype == 'url':
        result = value
    elif datatype == 'quantity':
        result = value['amount'] + ' ' + value['unit']
    elif datatype == 'time':
        result = value['time'] + ' ' + str(value['precision'])
    elif datatype == 'globe-coordinate':
        result = str(value['latitude']) + ' ' + str(value['longitude'])
    else:
        raise NotImplementedError()

    return result


def simple_recipe(recipe, entity, field):
    if field == 'sitelinks':
        value = 'title'
    else:
        value = 'value'

    if field not in recipe:
        return

    for r_label in recipe[field]:
        label = r_label.split()
        rule = label[0]

        if rule in entity[field]:
            if field == 'aliases':
                for alias in entity[field][rule]:
                    print(entity['id'], field, alias[value])
            elif field == 'claims':
                for claim in entity[field][rule]:
                    try:
                        print(entity['id'], rule, resolve_snak(claim))
                    except NotImplementedError:
                        pass
            else:
                print(entity['id'], field, entity[field][rule][value])
        else:
            if len(label) == 1:
                raise ValueError()


with gzip.open('1k.json.gz', 'rt') as fp_json:
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

        try:
            simple_recipe(recipe, entity, 'labels')
            simple_recipe(recipe, entity, 'descriptions')
            simple_recipe(recipe, entity, 'aliases')
            simple_recipe(recipe, entity, 'sitelinks')
            simple_recipe(recipe, entity, 'claims')
        except ValueError:
            continue

        found += 1

        #print(entity['labels']['en']['value'])
        #print("%s <<< %s" % (entity['id'], entity['claims']['P279'][0]['mainsnak']['datavalue']['value']['id']))

print("Wikidata entity found: %s/%s" % (found, counter))
