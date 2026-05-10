# Search & Indexing — Comprehensive Reference

> **Source files:**  
> - `machado/search_models.py` — PostgreSQL materialized search index model
> - `machado/forms.py` — `FeatureSearchForm` (PostgreSQL query generation)
> - `machado/views/search.py` — `FeatureSearchView` and export views
> - `machado/management/commands/rebuild_search_index.py` — Index population

---

## Architecture

Machado uses **PostgreSQL full-text search** natively (`tsvector`, `GIN` indexes, `pg_trgm`) via Django's `django.contrib.postgres.search` module. It does not require any external search services like Elasticsearch.

```
User query → FeatureSearchForm → Django ORM (SearchQuery) → PostgreSQL 15+
                                                                ↓
                                      ← FeatureSearchIndex model rows ← GIN Index
```

---

## PostgreSQL Search Index (`FeatureSearchIndex`)

To maintain high performance without hammering the relational Chado schema, Machado uses a materialized search table that denormalizes the data required for searching and faceting.

### Model Definition

Located in `machado/search_models.py`.

```python
class FeatureSearchIndex(models.Model):
    feature = models.OneToOneField(Feature, on_delete=models.CASCADE, primary_key=True)
    search_vector = SearchVectorField(null=True)       # GIN-indexed full-text vector
    autocomplete_text = models.TextField(default="")   # Raw text for trigram/prefix search
    ...
```

### Indexed Fields

#### Search Fields

| Field | Type | Description |
|---|---|---|
| `search_vector` | `SearchVectorField` | Primary full-text search column (English config). Aggregates: feature name, dbxrefs, GO terms, protein matches, annotations, DOIs, etc. |
| `autocomplete_text` | `TextField` | Raw text used for API autocomplete endpoints. |

#### Scalar Facet Fields

Stored as standard columns with b-tree indexes for fast `GROUP BY` counts.

| Field | Type | Description |
|---|---|---|
| `organism` | `CharField` | `"{genus} {species} [{infraspecific}]"` |
| `so_term` | `CharField` | Sequence Ontology type name |
| `uniquename` | `CharField` | Feature unique identifier |
| `orthology` | `BooleanField` | Has orthologous group assignment |
| `orthologous_group` | `CharField` | Orthologous group ID (conditional) |
| `coexpression` | `BooleanField` | Has co-expression group assignment |
| `coexpression_group` | `CharField` | Co-expression group ID (conditional) |

#### Array Facet Fields

Stored as `JSONField` arrays in PostgreSQL.

| Field | Type | Description |
|---|---|---|
| `analyses` | `JSONField` | Analysis program names (BLAST, InterProScan) |
| `doi` | `JSONField` | Publication DOIs |
| `biomaterial` | `JSONField` | RNA-seq biomaterial descriptions |
| `treatment` | `JSONField` | RNA-seq treatment names |
| `orthologs_coexpression`| `JSONField` | Array of booleans representing coexpression state of orthologs |

---

## Search Form (`FeatureSearchForm`)

Located in `machado/forms.py`. Responsible for translating user input into Django ORM queries against `FeatureSearchIndex`.

### Query Processing

```python
def search(self, selected_facets=None):
    qs = FeatureSearchIndex.objects.select_related("feature").all()
    
    if q:
        query = SearchQuery(q, config="english", search_type="websearch")
        qs = qs.filter(search_vector=query).annotate(
            rank=SearchRank("search_vector", query)
        ).order_by("-rank")
        
    # Apply facets...
    return qs
```

### Facet Logic

| Facet | Logic | Database Implementation |
|---|---|---|
| `analyses` | **AND (intersection)** | `qs.filter(analyses__contains=[v1]).filter(analyses__contains=[v2])` |
| Array fields | **OR (union)** | `Q(doi__contains=[v1]) \| Q(doi__contains=[v2])` |
| Scalar fields| **OR (union)** | `qs.filter(so_term__in=[v1, v2])` |

### Query Syntax

Machado uses PostgreSQL's `websearch` query type, which natively supports intuitive syntax similar to web search engines:
- `foo bar` — matches both words (unquoted)
- `"foo bar"` — matches exact phrase
- `foo -bar` — matches `foo` but excludes `bar`
- `foo OR bar` — matches either word

---

## Search Views (`FeatureSearchView`)

Located in `machado/views/search.py`.

### Configuration

The view defines a `FACET_FIELDS` dictionary mapping internal field names to user-friendly display labels.

### Facet Count Computation

To generate facet counts dynamically, the view performs database aggregations.

**Scalar Facets:** Computed using standard Django ORM `values().annotate(Count())`.
```python
qs.values(field).annotate(count=Count("pk")).order_by(field)[:100]
```

**Array Facets:** Computed using raw SQL with PostgreSQL's `jsonb_array_elements_text()` function to unnest the arrays before grouping and counting.
```sql
SELECT val, COUNT(*) FROM machado_featuresearchindex,
jsonb_array_elements_text(field) AS val WHERE feature_id IN (...) GROUP BY val
```

### Features

- **Pagination:** 50 results per page (configurable via `records` parameter)
- **Sorting:** Toggle via `order_by` parameter (defaults to relevance rank if a search term is provided)
- **Exporting:** `FeatureSearchExportView` streams results directly as TSV or FASTA without pagination limits.

---

## Template Tags for Search

The `machado_extras` template tag library provides URL manipulation helpers for the frontend search UI:

| Tag | Usage | Description |
|---|---|---|
| `{% param_replace key=value %}` | Add/replace URL parameter | Handles `selected_facets` (append), `order_by` (toggle direction), others (replace) |
| `{% remove_query %}` | Clear search query | Removes `q` parameter, preserves facets |
| `{% remove_facet "facet_name" %}` | Remove specific facet | Removes matching entries from `selected_facets` |
| `{% remove_facet_field "field" %}` | Remove entire facet category | Removes all entries starting with the field name |

---

## Index Management

Because the search index is a materialized table (`FeatureSearchIndex`), it must be populated after data is loaded into the main Chado tables.

```bash
# Build or rebuild the search index
python manage.py rebuild_search_index
```

### Performance Considerations

- The `rebuild_search_index` command gathers data from across the normalized Chado schema. For large databases, this can take a few minutes. It uses `--batch-size` (default 1000) for efficient bulk inserts.
- A `GIN` index (`fsi_search_gin`) powers the fast full-text querying.
- The `search_vector` column is populated inside the database at the end of the rebuild process using PostgreSQL's `to_tsvector()`.
