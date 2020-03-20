# wikidata-lite
We're collecting a lot of knowledge in Wikidata and this is awesome. Some of us also want to use it in some weird projects. Unfortunately [Wikidata RDF dumps](https://dumps.wikimedia.org/wikidatawiki/entities/) are really huge. Even the official SPARQL endpoint is under pressure by the incredible amount of data. At present time only simple queries or specific patterns see the light.

We need more light. So why we are here with Wikidata...lite!

In most of our use cases we don't need the entire sum of knowledge contained in the full graph. Probably we just need the tip of the iceberg. The idea behind this repository is to create simple recipes, with less fat and more of what you like!
So you can generate only the portion of the Wikidata RDF graph you need, reducing the cost of hardware and increasing the feasibility of your queries.

## Setup
You need Python 3+ and a JSON Wikidata dump ([latest-all.json.gz](https://dumps.wikimedia.org/wikidatawiki/entities/latest-all.json.gz) is the one we suggest).
```
pip install -r requirements.txt
```

## Usage
```
python wikidata-lite.py recipe wikidata rdf
```
Where:
- **recipe** is a valid YAML recipe (see paragraph "Recipes" for more details);
- **wikidata** is the path of your Wikidata dump (json.gz);
- **rdf** is the path for the RDF result (serialized as N-Triples).

## Recipes
Wikidata-lite uses a semantic YAML file as configuration. See recipe examples in [this directory](https://github.com/synapta/wikidata-lite/tree/master/recipe_examples) for inspiration. 

### Whitelist

With an empty recipe, you got an empty RDF. So you need to write which ingredients you want to be cooked!

You can add as many rules as you want for each category described below. An entity must have all the ingredients you choose (unless they are followed by `optional`) to be taken and is entirely skipped if it hasn't.

- **labels**: language-iso-code [optional]
- **descriptions**: language-iso-code [optional]
- **aliases**: language-iso-code [optional]
- **sitelinks**: wikiproject-code [optional]
- **claims**: predicate [optional]

### Blacklist

You can also add filter rules. So all the entities with at least one of the patterns expressed here are skipped.

- **filters**: predicate object

## Caveat

Although minimized, there may be small differences with the original RDF ontology. Moreover, we do not currently support all datatype nor qualifiers.

Datatype currently supported:
* wikibase-item
* external-id
* commonsMedia
* string
* url
* quantity
* time
* globe-coordinate
