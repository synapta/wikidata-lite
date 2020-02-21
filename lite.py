import bz2
import json

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

counter = 0;
found = 0;
print("Wikidata entity found: %s/%s" % (found, counter))

with bz2.open('wikidata.json.bz2', 'rt') as fp_json:
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

        if 'claims' not in entity:
            continue

        if 'labels' not in entity:
            continue

        if 'en' not in entity['labels']:
            continue

        # subclass of
        if 'P279' not in entity['claims']:
            continue

        found += 1

        #print(entity['labels']['en']['value'])
        #print("%s <<< %s" % (entity['id'], entity['claims']['P279'][0]['mainsnak']['datavalue']['value']['id']))

print("Wikidata entity found: %s/%s" % (found, counter))
