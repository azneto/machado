# Index and Search

## PostgreSQL Full-Text Search

Machado uses the native **full-text search capabilities of PostgreSQL** to provide fast, reliable search and faceted navigation without requiring any external search services. All search indexes are stored within the main database.



```bash
MACHADO_VALID_TYPES=gene,mRNA,polypeptide
```

If `MACHADO_VALID_TYPES` is not explicitly set in the settings, the default is `['gene', 'mRNA', 'polypeptide']`.

## Indexing the Data

The search system relies on a denormalized "materialized" index table to guarantee fast responses. After loading data into the Chado database, you must build the search index to make the new records searchable:

```bash
python manage.py rebuild_search_index
```

> **Note:** It is necessary to run `rebuild_search_index` whenever additional data is loaded into the database or when you wish to refresh the search facets.

Rebuilding the index queries the underlying database tables and batch-inserts the records into the search index. You can control the batch size to tune performance:

```bash
# Process 5,000 records at a time
python manage.py rebuild_search_index --batch-size 5000
```

## Search Features

The PostgreSQL search backend supports advanced search queries natively using "websearch" syntax:

* `gene kinase` — searches for documents containing both words
* `"receptor kinase"` — searches for the exact phrase
* `kinase -receptor` — searches for "kinase" but excludes documents containing "receptor"
* `kinase OR receptor` — searches for either word

All exported data (TSV or FASTA) from the search page is unlimited; PostgreSQL handles exporting the full result set regardless of its size.
