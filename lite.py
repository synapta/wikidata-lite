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

with gzip.open('100k.json.gz', 'rt') as fp_json:
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

        stop = False

        for r_label in recipe['label']:
            label = r_label.split()
            language = label[1]

            if language in entity['labels']:
                print(entity['labels'][language]['value'])
            else:
                if len(label) == 2:
                    stop = True
                    break

        if stop:
            continue

        found += 1

        #print(entity['labels']['en']['value'])
        #print("%s <<< %s" % (entity['id'], entity['claims']['P279'][0]['mainsnak']['datavalue']['value']['id']))

print("Wikidata entity found: %s/%s" % (found, counter))
