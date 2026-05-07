# Index and Search

## Haystack

The [Haystack](https://haystacksearch.org) software enables the Django framework to run third party search engines such as Elasticsearch and Solr. Even though you can use any search engine supported by Haystack, machado was tested using [Elasticsearch](https://www.elastic.co/products/elasticsearch).

## Install Elasticsearch

Elasticsearch 7.x is required. Install Java first:

```bash
sudo apt install openjdk-11-jdk
```

Then install Elasticsearch:

```bash
wget https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-7.17.26-amd64.deb
sudo dpkg -i elasticsearch-7.17.26-amd64.deb
sudo systemctl daemon-reload
sudo systemctl enable elasticsearch.service
sudo systemctl start elasticsearch.service
```

Install the Python client inside your virtualenv:

```bash
pip install 'elasticsearch>=7,<8'
```

## Enable Search in machado

Uncomment the Elasticsearch settings in your `.env` file:

```bash
ELASTICSEARCH_URL=http://127.0.0.1:9200/
HAYSTACK_INDEX_NAME=haystack
```

When `ELASTICSEARCH_URL` is set, machado automatically adds `haystack` to `INSTALLED_APPS` and configures `HAYSTACK_CONNECTIONS` — no manual editing of `settings.py` is needed.

You can also configure which feature types are indexed:

```bash
MACHADO_VALID_TYPES=gene,mRNA,polypeptide
```

If `MACHADO_VALID_TYPES` is not set, the default is `gene,mRNA,polypeptide`.

## Indexing the Data

After loading data into the database, build the search index:

```bash
python manage.py rebuild_index
```

> **Note:** It is necessary to run `rebuild_index` whenever additional data is loaded into the database or when search-related settings change.

Rebuilding the index can be faster if you increase the number of workers:

```bash
python manage.py rebuild_index -k 4
```

## Increasing the Results Limit

The Elasticsearch server has a 10,000 results limit by default. In most cases it will not affect the results since they are paginated. The links to export `.tsv` or `.fasta` files might be truncated because of this limit. You can increase it with:

```bash
curl -XPUT "http://localhost:9200/haystack/_settings" \
     -d '{ "index" : { "max_result_window" : 500000 } }' \
     -H "Content-Type: application/json"
```
