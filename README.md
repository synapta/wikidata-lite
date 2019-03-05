# wikidata-lite
We're collecting lot of knowledge in Wikidata and this is awsome. Some of us also want to use it in some weird project.
Unfortunately Wikidata RDF dumps (https://dumps.wikimedia.org/wikidatawiki/entities/) are really big.
Even the official SPARQL endpoint is under pressure by the huge amount of data under it. At the present time only simple queries or
specific patterns see the light.

We need more light. So why we need a Wikidata...lite!

In most of our use cases we don't need the entire sum of knowledge contained in the full graph.
Probably we just need the tip of the iceberg.
The idea behind this repository is to create simple receipes, with less fats and more of what you like!
So you can generate only the portion of Wikidata graph you need, reducing the cost of hardware and increasing the feasibility of your queries.

## Setup
TODO

## Usage
```
./wd-lite.sh recipe inputfile outputfile
```
Where:
- recipe is a YAML file like in examples
- inputfile is the path of your Wikidata dump (nt.gz)
- outputfile is the path of the nt RDF result

### Configuration file
Wikidata-lite use a semantic YAML file as configuration. For each category described below you can choose an `add` or `not` rule, for
a specific characteristic, using eventually `optional` (among `add`). You can add as many rules as you want for each category.

- label: add language [optional]
- description: add language [optional]
- predicate: (add|rm) PXX [optional]
- predicate-object: (add|rm) PXX QXX [optional]
