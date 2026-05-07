# Web Interface & Views

> **Source files:**  
> - `machado/views/common.py` — Home and data summary views  
> - `machado/views/feature.py` — Feature detail view  
> - `machado/views/search.py` — Search and export views  
> - `machado/templates/` — 10 HTML templates  
> - `machado/static/` — JavaScript assets  
> - `machado/templatetags/machado_extras.py` — Custom template tags

---

## URL Routing (`machado/urls.py`)

| URL Pattern | View | Name | Description |
|---|---|---|---|
| `/` | `index` | `index` | Home page |
| `/data/` | `data` | `data` | Data summary per organism |
| `/feature/` | `feature` | `feature` | Feature detail page |
| `/find/` | `MachadoFacetedSearchView` | `haystack_search` | Faceted search |
| `/export/` | `MachadoExportView` | `export` | Search results export |
| `/api/` | DRF Router | — | REST API endpoints |
| `/account/` | Account views | — | User authentication |

---

## Views

### Home View (`views/common.py`)

```python
def index(request):
```

**Behavior:**
- Checks if Haystack search is configured
- If yes → renders `index.html` with search form
- If no → renders `congrats.html` with data counts:
  - Total organisms
  - Total features
  - Total publications
  - Total analyses

### Data Summary View (`views/common.py`)

```python
def data(request):
```

**Renders:** `data-numbers.html` with per-organism feature counts grouped by SO term.

### Feature Detail View (`views/feature.py`)

```python
def feature(request):
```

**Parameters:** `feature_id` (GET parameter)

**Process:**
1. Retrieves `Feature` by `feature_id`
2. Checks presence of related data:
   - `has_ontology` — FeatureCvterm exists
   - `has_ortholog` — orthologous group property exists
   - `has_expression` — Analysisfeature with normscore exists
   - `has_coexpression` — coexpression group property exists
   - `has_proteinmatches` — protein_match relationships exist
   - `has_similarity` — similarity analysis features exist
   - `has_publication` — FeaturePub exists
3. Renders `feature.html` with all presence flags

### Search View (`views/search.py`)

```python
class MachadoFacetedSearchView(FacetedSearchView):
```

**Facet configuration:**

| Facet Key | Display Label | Description |
|---|---|---|
| `organism` | Organism | Species filter |
| `so_term` | Type | Feature type (gene, mRNA, etc.) |
| `analyses` | Analysis | BLAST/InterProScan results |
| `orthology` | Orthology | Has ortholog group |
| `orthologous_group` | Ortholog group | Specific group ID |
| `coexpression` | Co-expression | Has co-expression group |
| `coexpression_group` | Co-expression group | Specific group ID |
| `biomaterial` | Biomaterial | RNA-seq sample |
| `treatment` | Treatment | Experimental treatment |
| `doi` | DOI | Publication DOI |

**Pagination:** 50 results per page  
**Sorting:** Toggleable via `order_by` parameter  

### Export View (`views/search.py`)

```python
class MachadoExportView(FacetedSearchView):
```

**Output formats:**
- **TSV:** `organism | SO_term | uniquename | name | display`
- **FASTA:** Header with organism/type/name, sequence body

**Content type:** `text/tab-separated-values`

---

## Templates

### `base.html` (3 KB)

Base layout template. Provides:
- HTML5 doctype with `lang="en"`
- Bootstrap CSS/JS CDN includes
- jQuery CDN include
- Navigation bar with search form
- Footer block
- Block definitions: `title`, `content`, `extra_js`

### `index.html` (1.5 KB)

Home page when Haystack is configured:
- Search input form
- Data summary link
- Welcome text block

### `congrats.html` (2.6 KB)

Setup confirmation page (no Haystack):
- Displays counts: organisms, features, publications, analyses
- Instructions for enabling search
- Links to documentation

### `data-numbers.html` (1.5 KB)

Data summary page:
- Per-organism table
- Feature counts by SO term
- Total counts row

### `feature.html` (7.8 KB)

Feature detail page — the most complex template:
- Feature header (uniquename, name, organism, SO term)
- Tab navigation for sub-sections:
  - **Info** — general information (loaded via API)
  - **Ontology** — GO terms and other CV associations
  - **Orthology** — orthologous group members
  - **Expression** — RNA-seq expression data
  - **Co-expression** — co-expression group members
  - **Protein matches** — InterProScan domain hits
  - **Similarity** — BLAST/Diamond results
  - **Publication** — linked publications
- Tabs are conditionally shown based on `has_*` flags
- Content loaded dynamically via JavaScript API calls

### `search_result.html` (5.3 KB)

Search results page:
- Results count and pagination
- Sort controls (toggleable direction)
- Result list with feature links
- Includes `search_form.html` and `search_facet.html`

### `search_form.html` (514 B)

Search input partial:
- Text input with autocomplete
- Submit button
- Hidden fields for preserving facet selections

### `search_facet.html` (5.9 KB)

Facet sidebar partial:
- Collapsible facet groups
- Active facet display with remove buttons
- Facet value counts
- Uses `param_replace` and `remove_facet_field` template tags

### `search_result.out` (673 B)

Export template:
- TSV format output
- Header row
- Iterates over search results

### `error.html` (351 B)

Error display page:
- Error message display
- Back navigation link

---

## JavaScript Assets

### `feature.js` (9.5 KB)

Feature detail page interactivity:
- **API data loading** — fetches feature info, ontology, orthology, expression, co-expression, protein matches, similarity, and publication data via AJAX calls to the REST API
- **Dynamic tab rendering** — populates tab content from API responses
- **DataTables integration** — renders tabular data with sorting and pagination
- **Expression charts** — visualizes RNA-seq expression data
- **JBrowse links** — generates genome browser links from location data

### `main.js` (857 B)

General page functionality:
- Autocomplete initialization for search input
- Global event handlers

---

## Template Tags (`machado_extras.py`)

### Tags

| Tag | Type | Description |
|---|---|---|
| `{% param_replace key=value %}` | `simple_tag` | Manipulates URL query parameters. Special handling: `selected_facets` (appends), `order_by` (toggles `-` prefix for sort direction) |
| `{% remove_query %}` | `simple_tag` | Clears the `q` parameter from URL |
| `{% remove_facet "facet" %}` | `simple_tag` | Removes a specific facet value from `selected_facets` list |
| `{% remove_facet_field "field" %}` | `simple_tag` | Removes all values for a facet field from `selected_facets` |

### Filters

| Filter | Description |
|---|---|
| `{{ dict\|get_item:key }}` | Dictionary value lookup |
| `{{ dict\|get_count:key }}` | Count of items in dictionary value |
| `{{ value\|split:"," }}` | Split string by delimiter |

---

## Configuration & Auto-Patching

The `machado/settings.py` module and `MachadoConfig.ready()` in `apps.py` automatically patch Django settings on startup:

### Middleware Additions

```python
django.contrib.sessions.middleware.SessionMiddleware
django.contrib.auth.middleware.AuthenticationMiddleware
django.contrib.messages.middleware.MessageMiddleware
```

### Template Configuration

If `TEMPLATES` is empty, configures:
```python
TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [],
    'APP_DIRS': True,
    'OPTIONS': {
        'context_processors': [
            'django.template.context_processors.debug',
            'django.template.context_processors.request',
            'django.contrib.auth.context_processors.auth',
            'django.contrib.messages.context_processors.messages',
        ],
    },
}]
```

### URL Merging

Merges Machado's URL patterns into the project's `ROOT_URLCONF` module.

### Other Settings

| Setting | Value | Purpose |
|---|---|---|
| `USE_THOUSAND_SEPARATOR` | `True` | Number formatting in templates |
| `APPEND_SLASH` | `True` | URL normalization |
| `USE_X_FORWARDED_HOST` | `True` | Reverse proxy support |
| `SECURE_PROXY_SSL_HEADER` | `('HTTP_X_FORWARDED_PROTO', 'https')` | SSL proxy detection |
| `SWAGGER_SETTINGS['USE_SESSION_AUTH']` | `False` | Swagger UI auth mode |
