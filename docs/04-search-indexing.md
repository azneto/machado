# Search & Indexing — Comprehensive Reference

> **Source files:**  
> - `machado/search_indexes.py` — Elasticsearch index definition (301 lines)  
> - `machado/forms.py` — FacetedSearchForm (57 lines)  
> - `machado/views/search.py` — Search/export views (119 lines)

---

## Architecture

Machado uses **django-haystack 3.3.x** with **Elasticsearch 7.17** for full-text search and faceted navigation.

```
User query → FacetedSearchForm → Haystack SearchQuerySet → Elasticsearch 7
                                                              ↓
                                     ← SearchResult objects ← Index (FeatureIndex)
```

---

## Elasticsearch Index (`FeatureIndex`)

### Model Binding

```python
class FeatureIndex(indexes.SearchIndex, indexes.Indexable):
    class Meta:
        model = Feature
```

### Index Queryset

Only indexes features that:
1. Match types in `settings.MACHADO_VALID_TYPES` (e.g., `["gene", "mRNA", "polypeptide"]`)
2. Belong to `cv.name = "sequence"`
3. Have `is_obsolete = False`

```python
def get_model(self):
    return Feature

def index_queryset(self, using=None):
    return self.get_model().objects.filter(
        type__name__in=settings.MACHADO_VALID_TYPES,
        type__cv__name="sequence",
        is_obsolete=False,
    )
```

### Indexed Fields

#### Document Field (full-text)

| Field | Type | Description |
|---|---|---|
| `text` | `CharField(document=True, use_template=True)` | Primary search field. Aggregates: feature name, uniquename, dbxrefs, GO terms, protein matches, annotations, DOIs, expression sample names, overlapping feature names |

#### Facet Fields

| Field | Type | Faceted | Description |
|---|---|---|---|
| `organism` | `CharField` | ✅ | `"{genus} {species} [{infraspecific}]"` |
| `so_term` | `CharField` | ✅ | Sequence Ontology type name (gene, mRNA, etc.) |
| `uniquename` | `CharField` | ✅ | Feature unique identifier |
| `name` | `CharField` | ✅ | Feature display name |
| `display` | `CharField` | ✅ | Display text from `get_display()` |
| `analyses` | `MultiValueField` | ✅ | Analysis program names (BLAST, InterProScan, etc.) |
| `doi` | `MultiValueField` | ✅ | Publication DOIs |
| `biomaterial` | `MultiValueField` | ✅ | RNA-seq biomaterial descriptions |
| `treatment` | `MultiValueField` | ✅ | RNA-seq treatment names |
| `orthology` | `BooleanField` | ✅ | Has orthologous group assignment |
| `orthologous_group` | `CharField` | ✅ | Orthologous group ID (conditional) |
| `coexpression` | `BooleanField` | ✅ | Has co-expression group assignment |
| `coexpression_group` | `CharField` | ✅ | Co-expression group ID (conditional) |

#### Autocomplete Field

| Field | Type | Description |
|---|---|---|
| `autocomplete` | `EdgeNgramField` | Organism prefix + full text for typeahead. Uses EdgeNgram for prefix matching |

#### Relationship Field

| Field | Type | Description |
|---|---|---|
| `relationship` | `MultiValueField` | Related feature IDs and types (parent/child via part_of) |

### Data Preparation Methods

The `FeatureIndex` class contains `prepare_*` methods for each field:

```python
def prepare_organism(self, obj):
    """Build organism display string."""
    organism = "{} {}".format(obj.organism.genus, obj.organism.species)
    if obj.organism.infraspecific_name:
        organism += " {}".format(obj.organism.infraspecific_name)
    return organism

def prepare_analyses(self, obj):
    """Collect analysis program names from FeatureRelationship → Analysisfeature."""
    # Returns list of unique program names linked via similarity relationships

def prepare_text(self, obj):
    """Aggregate all searchable text."""
    # Combines: name, uniquename, dbxrefs, GO terms, protein matches,
    # annotations, DOIs, expression samples, overlapping features
```

### Conditional Fields

The `orthology`, `orthologous_group`, `coexpression`, and `coexpression_group` fields are **conditionally indexed** — they are only populated if the corresponding featureprop values exist for the feature.

---

## Search Form (`FeatureSearchForm`)

### Class: `FeatureSearchForm(FacetedSearchForm)`

Extends Haystack's `FacetedSearchForm` with custom facet processing.

### Query Processing

```python
def search(self):
    sqs = super().search()

    # Process selected facets
    for facet in self.selected_facets:
        field, value = facet.split(":", 1)

        # Escape special Elasticsearch characters
        value = value.replace(":", "\\:")
        value = value.replace("/", "\\/")
        value = value.replace(".", "\\.")
        value = value.replace('"', '\\"')

        # Apply facet narrowing
        if field == "analyses_exact":
            sqs = sqs.narrow('analyses_exact:"{}"'.format(value))  # AND logic
        else:
            sqs = sqs.narrow('{}:"{}"'.format(field, value))       # OR logic
```

### Facet Logic

| Facet | Logic | Behavior |
|---|---|---|
| `analyses` | **AND (intersection)** | All selected analysis types must be present |
| All others | **OR (union)** | Any selected value matches |

### Character Escaping

The form escapes these characters before sending to Elasticsearch:
- `:` → `\\:`
- `/` → `\\/`
- `.` → `\\.`
- `"` → `\\"`

---

## Search View (`MachadoFacetedSearchView`)

### Configuration

```python
FACET_FIELDS = [
    ("organism", "Organism"),
    ("so_term", "Type"),
    ("analyses", "Analysis"),
    ("orthology", "Orthology"),
    ("orthologous_group", "Ortholog group"),
    ("coexpression", "Co-expression"),
    ("coexpression_group", "Co-expression group"),
    ("biomaterial", "Biomaterial"),
    ("treatment", "Treatment"),
    ("doi", "DOI"),
]
```

### Features

- **Pagination:** 50 results per page (configurable via `paginate_by`)
- **Sorting:** Toggle ascending/descending via `order_by` URL parameter
- **Facet ordering:** Alphabetical within each facet category
- **Context data:** Injects `facet_fields_info` mapping for template rendering

### Export View (`MachadoExportView`)

Exports search results in TSV or FASTA format:
- **TSV:** `organism | SO_term | uniquename | name | display`
- **FASTA:** Standard FASTA format with feature metadata in header

---

## Template Tags for Search

The `machado_extras` template tag library provides URL manipulation helpers:

| Tag | Usage | Description |
|---|---|---|
| `{% param_replace key=value %}` | Add/replace URL parameter | Handles `selected_facets` (append), `order_by` (toggle direction), others (replace) |
| `{% remove_query %}` | Clear search query | Removes `q` parameter, preserves facets |
| `{% remove_facet "facet_name" %}` | Remove specific facet | Removes matching entries from `selected_facets` |
| `{% remove_facet_field "field_exact" %}` | Remove entire facet category | Removes all entries starting with the field name |

---

## Elasticsearch Configuration

### Required Settings

```python
HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.elasticsearch7_backend.Elasticsearch7SearchEngine',
        'URL': 'http://127.0.0.1:9200/',
        'INDEX_NAME': 'haystack',
    },
}

MACHADO_VALID_TYPES = ['gene', 'mRNA', 'polypeptide']
```

### Index Management Commands

```bash
# Build/rebuild the entire search index
python manage.py rebuild_index

# Update only changed records
python manage.py update_index

# Clear the search index
python manage.py clear_index
```

### Performance Considerations

- Index rebuilds can be slow for large datasets — use `--batch-size` parameter
- The `autocomplete` EdgeNgram field increases index size but enables fast typeahead
- `MultiValueField` facets (analyses, doi, biomaterial, treatment) support multiple values per document
- The `prepare_text()` method performs extensive ORM queries — consider database query optimization for large indexes
