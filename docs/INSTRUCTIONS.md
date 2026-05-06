# Machado — Complete Software Specification

> **Version:** 0.5.0  
> **License:** GNU GPLv3  
> **Copyright:** 2018 Embrapa (Brazilian Agricultural Research Corporation)  
> **Repository:** https://github.com/lmb-embrapa/machado  
> **Documentation:** http://machado.readthedocs.io  
> **Citation:** GigaScience, Volume 9, Issue 9, September 2020 — DOI: 10.1093/gigascience/giaa097

---

## Detailed Documentation

This specification is supplemented by in-depth reference files for each major subsystem:

| File | Section | Description |
|---|---|---|
| [01-database-models.md](01-database-models.md) | §4 | All Chado ORM models, field details, decorator-injected methods |
| [02-data-loaders.md](02-data-loaders.md) | §5 | Loader library internals, management command arguments, loading order |
| [03-rest-api.md](03-rest-api.md) | §6–§7 | All REST endpoints with request/response examples |
| [04-search-indexing.md](04-search-indexing.md) | §8 | Elasticsearch index fields, faceted search logic, query processing |
| [05-web-interface.md](05-web-interface.md) | §9–§10 | Views, templates, JavaScript, template tags, auto-patching |
| [06-testing-cicd-deployment.md](06-testing-cicd-deployment.md) | §11–§14 | Test suite, CI pipeline, deployment, configuration reference |

---

## 1. Overview

Machado is a **Django application** that provides a Python/web interface to a **Chado** biological database schema (v1.31). It enables researchers to **store, search, and visualize** genomic and biological data through:

- CLI-based data loaders for standard bioinformatics file formats
- A REST API serving data to the JBrowse genome browser
- Full-text search powered by Haystack + Elasticsearch
- A web UI with faceted search, feature detail pages, and data summaries
- User authentication and management via token-based auth

The database schema is **unmanaged** (`managed = False`) — Machado maps Django ORM models onto an existing PostgreSQL Chado schema rather than creating its own tables.

---

## 2. Technology Stack

| Layer | Technology |
|---|---|
| Language | Python 3.10 / 3.11 / 3.12 |
| Framework | Django 5.1.x |
| Database | PostgreSQL 15+ (Chado schema v1.31) |
| ORM | Django ORM (unmanaged models) |
| REST API | Django REST Framework 3.15.x |
| API Docs | drf-yasg 1.21.8 (Swagger/OpenAPI) |
| Nested Routes | drf-nested-routers 0.94.x |
| Search | django-haystack 3.3.x + Elasticsearch 7.17 |
| Bioinformatics | BioPython 1.84, pysam 0.22.x, obonet 1.1.x |
| Ontology Graphs | NetworkX 3.3 |
| Bibliography | bibtexparser 1.4.x |
| Progress Bars | tqdm 4.66.x |
| DB Driver | psycopg2-binary 2.9.x |
| CI/CD | GitHub Actions (Linux, Python matrix) |
| Linting | flake8 + flake8-black |
| Docs | Sphinx via Read the Docs |
| Containerization | Docker (via machado-docker repo) |

---

## 3. Project Structure

```
azneto-machado/
├── bin/
│   └── fixChadoModel.py          # Post-inspectdb model fixer script
├── docs/                          # Sphinx documentation source
├── extras/
│   ├── sample.tar.gz              # Sample biological data
│   └── trackList.json.sample      # JBrowse configuration example
├── machado/                       # Main Django application package
│   ├── __init__.py                # App config reference
│   ├── apps.py                    # MachadoConfig (auto-patches settings)
│   ├── settings.py                # Dynamic Django settings patcher
│   ├── models.py                  # 4,350-line Chado ORM (unmanaged)
│   ├── decorators.py              # Feature/Pub method injectors
│   ├── forms.py                   # Haystack faceted search form
│   ├── urls.py                    # Root URL routing
│   ├── search_indexes.py          # Elasticsearch index definition
│   ├── account/                   # User auth module (login/logout/CRUD)
│   ├── api/                       # REST API (serializers, views, urls)
│   ├── loaders/                   # Data import modules (16 files)
│   ├── management/commands/       # Django CLI commands (33 commands)
│   ├── migrations/                # Django migrations
│   ├── schemas/1.31/              # Chado SQL schema + patches
│   ├── static/                    # JS assets (feature.js, main.js)
│   ├── templates/                 # HTML templates (10 files)
│   ├── templatetags/              # Custom Django template tags
│   ├── tests/                     # Unit tests (22 test files)
│   └── views/                     # Web views (common, feature, search)
├── setup.py                       # Package installation
├── setup.cfg
├── MANIFEST.in
├── LICENSE.txt                    # GPLv3
├── README.md
├── CONTRIBUTING.rst
├── CONTRIB.rst                    # Contributors list
├── .coveragerc
├── .flake8
├── .readthedocs.yaml
└── .github/
    ├── workflows/django.yml       # CI pipeline
    ├── ISSUE_TEMPLATE.md
    └── PULL_REQUEST_TEMPLATE.md
```

---

## 4. Database Layer — Chado ORM Models

### 4.1 Architecture

- **File:** `machado/models.py` (4,350 lines, 133 KB)
- **Pattern:** All models use `managed = False` — they map to pre-existing Chado PostgreSQL tables
- **Schema version:** Chado 1.31 (SQL in `machado/schemas/1.31/default_schema.sql`)
- **Primary keys:** `BigAutoField` throughout
- **Foreign keys:** `on_delete=models.DO_NOTHING` with explicit `related_name` pattern: `{ModelName}_{field}_{TargetModel}`

### 4.2 Core Model Groups

| Module | Key Tables | Purpose |
|---|---|---|
| **Controlled Vocabulary** | `Cv`, `Cvterm`, `CvtermRelationship`, `Cvtermsynonym`, `Cvtermprop`, `CvtermDbxref`, `Cvtermpath` | Ontology terms and relationships |
| **Database Cross-References** | `Db`, `Dbxref`, `Dbxrefprop` | External database references |
| **Organism** | `Organism`, `OrganismDbxref`, `Organismprop`, `OrganismPub` | Species/strain records |
| **Sequence/Feature** | `Feature`, `Featureloc`, `FeatureRelationship`, `Featureprop`, `FeatureCvterm`, `FeatureDbxref`, `FeaturePub`, `FeatureSynonym` | Genomic features and annotations |
| **Analysis** | `Analysis`, `Analysisfeature`, `Analysisprop`, `AnalysisRelationship` | Computational analyses (BLAST, InterProScan) |
| **Publication** | `Pub`, `PubDbxref`, `Pubauthor`, `Pubprop`, `PubRelationship` | Literature references |
| **Phylogeny** | `Phylotree`, `Phylonode`, `PhylonodeRelationship` | Phylogenetic trees |
| **Expression** | `Assay`, `Biomaterial`, `Acquisition`, `Quantification`, `Treatment` | RNA-seq expression data |
| **Stock/Natural Diversity** | `Stock`, `Stockprop`, `NdExperiment`, `NdGeolocation` | Germplasm and experiments |
| **Genotype/Phenotype** | `Genotype`, `Phenotype`, `FeatureGenotype`, `FeaturePhenotype` | Variant and phenotype data |

### 4.3 Decorator-Injected Methods

The `decorators.py` module dynamically attaches methods to `Feature` and `Pub` models:

**Feature methods:**
- `get_display()` — returns display/product/description/note (priority chain)
- `get_product()`, `get_description()`, `get_note()` — specific featureprop accessors
- `get_annotation()` — annotations with optional DOI references
- `get_doi()` — publication DOIs linked to the feature
- `get_dbxrefs()` — external database cross-references with URL links
- `get_orthologous_group()`, `get_coexpression_group()` — cluster membership
- `get_expression_samples()` — RNA-seq expression with biomaterial/treatment metadata
- `get_relationship()` — parent/child features via `part_of`/`translation_of`
- `get_cvterm()` — associated ontology terms (GO, etc.)
- `get_location()` — genomic coordinates with JBrowse URL generation
- `get_properties()` — all feature properties
- `get_synonyms()` — feature synonyms

**Pub methods:**
- `get_authors()` — formatted author string
- `get_doi()` — publication DOI accession

---

## 5. Data Loaders

### 5.1 Loader Library (`machado/loaders/`)

| Module | Classes | Purpose |
|---|---|---|
| `common.py` | `FileValidator`, `FieldsValidator` | Input validation; organism/feature/cvterm retrieval helpers |
| `exceptions.py` | `ImportingError` | Custom exception for import failures |
| `ontology.py` | `OntologyLoader` | OBO ontology parsing (terms, typedefs, relationships, synonyms, xrefs) |
| `feature.py` | `FeatureLoaderBase`, `FeatureLoader`, `MultispeciesFeatureLoader` | GFF3/VCF feature import, annotation, dbxrefs, relationships, orthology groups |
| `featureattributes.py` | `FeatureAttributesLoader` | GFF attribute parsing (GO terms, Dbxrefs, Ontology_term, etc.) |
| `similarity.py` | `SimilarityLoader` | BLAST/InterProScan result import with match_part features |
| `sequence.py` | — | FASTA sequence loading |
| `organism.py` | — | Organism record management |
| `publication.py` | — | BibTeX publication import |
| `analysis.py` | `AnalysisLoader` | Analysis record and analysisfeature management |
| `phylotree.py` | — | Phylogenetic tree import |
| `biomaterial.py` | — | Biomaterial/sample records |
| `assay.py` | — | Assay/experiment records |
| `project.py` | — | Project records |
| `treatment.py` | — | Treatment records |

### 5.2 Management Commands (`machado/management/commands/`)

**Data Loading (20 commands):**

| Command | Input Format | Description |
|---|---|---|
| `load_relations_ontology` | OBO | Load Relations Ontology (RO) |
| `load_sequence_ontology` | OBO | Load Sequence Ontology (SO) |
| `load_gene_ontology` | OBO | Load Gene Ontology (GO) — supports `--cpu` parallelism |
| `insert_organism` | CLI args | Register a single organism (genus, species, infraspecific) |
| `load_organism` | TSV | Bulk organism import |
| `load_fasta` | FASTA | Load reference sequences (chromosomes, scaffolds) with `--soterm` |
| `load_gff` | GFF3 (bgzipped+tabixed) | Load genomic features — supports `--cpu` parallelism, `--qtl` mode |
| `load_feature_annotation` | TSV | Add annotations (display, product, etc.) to features |
| `load_feature_dbxrefs` | TSV | Add database cross-references to features |
| `load_feature_publication` | TSV | Link features to publications via DOI |
| `load_feature_sequence` | FASTA | Attach sequences to existing features |
| `load_similarity` | BLAST-XML / InterProScan-XML | Load similarity search results |
| `load_similarity_matches` | TSV | Load pre-processed similarity matches |
| `load_publication` | BibTeX | Import publications |
| `load_organism_publication` | TSV | Link organisms to publications |
| `load_orthomcl` | OrthoMCL groups | Load orthology group assignments |
| `load_phylotree` | Newick | Load phylogenetic trees |
| `load_rnaseq_info` | TSV | Load RNA-seq experiment metadata |
| `load_rnaseq_data` | TSV | Load RNA-seq expression values |
| `load_vcf` | VCF (bgzipped+tabixed) | Load variant data (SNVs, indels) |
| `load_coexpression_clusters` | TSV | Load co-expression cluster assignments |
| `load_coexpression_pairs` | TSV | Load co-expression gene pairs |
| `check_ids` | — | Validate feature IDs |

**Data Removal (11 commands):**

| Command | Description |
|---|---|
| `remove_file` | Remove all data loaded from a specific file |
| `remove_analysis` | Remove analysis and associated features |
| `remove_feature_annotation` | Remove feature annotations |
| `remove_ontology` | Remove an ontology and its terms |
| `remove_organism` | Remove a single organism and its data |
| `remove_organisms` | Remove multiple organisms |
| `remove_phylotree` | Remove a phylogenetic tree |
| `remove_publication` | Remove a publication |
| `remove_relationship` | Remove feature relationships |

### 5.3 Typical Data Loading Workflow

```bash
# 1. Load ontologies (required first)
python manage.py load_relations_ontology --file ro.obo
python manage.py load_sequence_ontology --file so.obo
python manage.py load_gene_ontology --file go.obo --cpu 10

# 2. Register organism
python manage.py insert_organism --genus Arabidopsis --species thaliana

# 3. Load reference genome
python manage.py load_fasta --file genome.fa --soterm chromosome \
    --organism 'Arabidopsis thaliana'

# 4. Load features (GFF must be bgzipped and tabix-indexed)
python manage.py load_gff --file features.gff3.gz \
    --organism 'Arabidopsis thaliana' --cpu 10

# 5. Load annotations and cross-references
python manage.py load_feature_annotation --file annotations.txt \
    --soterm mRNA --cvterm display --organism 'Arabidopsis thaliana'

# 6. Build search index
python manage.py rebuild_index
```

---

## 6. REST API

### 6.1 Architecture

- **Framework:** Django REST Framework with `SimpleRouter`
- **Documentation:** Swagger UI via drf-yasg at `/api/`
- **Caching:** Configurable via `CACHE_TIMEOUT` setting (default: 3600s)

### 6.2 Read Endpoints

| Endpoint Pattern | ViewSet | Description |
|---|---|---|
| `api/jbrowse/stats/global` | `JBrowseGlobalViewSet` | JBrowse global stats |
| `api/jbrowse/features/{refseq}` | `JBrowseFeatureViewSet` | JBrowse feature tracks (filtered by `organism`, `soType`) |
| `api/jbrowse/names` | `JBrowseNamesViewSet` | JBrowse name autocomplete |
| `api/jbrowse/refSeqs.json` | `JBrowseRefSeqsViewSet` | JBrowse reference sequences |
| `api/autocomplete` | `autocompleteViewSet` | Search autocomplete |
| `api/organism/id` | `OrganismIDViewSet` | Organism by ID |
| `api/organism/list` | `OrganismListViewSet` | All organisms |
| `api/feature/id` | `FeatureIDViewSet` | Feature by ID |
| `api/feature/ontology/{id}` | `FeatureOntologyViewSet` | Feature ontology terms |
| `api/feature/ortholog/{id}` | `FeatureOrthologViewSet` | Feature orthologs |
| `api/feature/proteinmatches/{id}` | `FeatureProteinMatchesViewSet` | Protein domain matches |
| `api/feature/expression/{id}` | `FeatureExpressionViewSet` | Expression data |
| `api/feature/coexpression/{id}` | `FeatureCoexpressionViewSet` | Co-expression data |
| `api/feature/info/{id}` | `FeatureInfoViewSet` | Feature information |
| `api/feature/location/{id}` | `FeatureLocationViewSet` | Genomic location |
| `api/feature/publication/{id}` | `FeaturePublicationViewSet` | Related publications |
| `api/feature/sequence/{id}` | `FeatureSequenceViewSet` | Feature sequences |
| `api/feature/similarity/{id}` | `FeatureSimilarityViewSet` | Similarity results |
| `api/history` | `HistoryListViewSet` | Data loading history |

### 6.3 Load Endpoints (Programmatic Data Import)

| Endpoint | ViewSet | Description |
|---|---|---|
| `api/load/organism` | `OrganismViewSet` | Create organism |
| `api/load/relations_ontology` | `RelationsOntologyViewSet` | Load RO |
| `api/load/sequence_ontology` | `SequenceOntologyViewSet` | Load SO |
| `api/load/gene_ontology` | `GeneOntologyViewSet` | Load GO |
| `api/load/publication` | `PublicationViewSet` | Load publication |
| `api/load/fasta` | `FastaViewSet` | Load FASTA |
| `api/load/gff` | `GFFViewSet` | Load GFF |
| `api/load/feature_annotation` | `FeatureAnnotationViewSet` | Load annotation |
| `api/load/feature_sequence` | `FeatureSequenceViewSet` | Load sequence |
| `api/load/feature_dbxrefs` | `FeatureDBxRefViewSet` | Load dbxrefs |
| `api/load/feature_publication` | `FeaturePublicationViewSet` | Load feature-pub links |

### 6.4 JBrowse Integration

Machado serves as a **REST data backend** for JBrowse genome browser. Configuration sample in `extras/trackList.json.sample` shows tracks for:
- Reference sequences (chromosomes)
- Genes, Transcripts, CDS
- Variation (SNVs)

Settings: `MACHADO_JBROWSE_URL`, `MACHADO_JBROWSE_TRACKS`, `MACHADO_JBROWSE_OFFSET`

---

## 7. User Authentication System

### 7.1 Module: `machado/account/`

Token-based authentication using DRF's `TokenAuthentication`.

### 7.2 Endpoints

| Path | Method | Permission | Action |
|---|---|---|---|
| `account/login` | POST | Public | Authenticate by email+password, return token |
| `account/logout` | POST | Authenticated | Invalidate token |
| `account/` | GET | Admin | List all users |
| `account/` | POST | Admin | Create user |
| `account/{id}` | GET | Admin | Get user by ID |
| `account/{id}` | PUT | Admin | Update user |
| `account/{id}` | DELETE | Admin | Delete user |
| `account/username/{username}` | GET | Admin | Search by username |

### 7.3 Serializers

- **`UserSerializer`**: Read-only fields — `id`, `username`, `email`, `first_name`, `last_name`, `is_staff`
- **`UserCreateSerializer`**: Validates unique username/email, creates with `create_user()`, supports `is_staff` flag

---

## 8. Search & Indexing

### 8.1 Elasticsearch Index (`search_indexes.py`)

**Index class:** `FeatureIndex` on the `Feature` model.

**Indexed fields:**

| Field | Type | Description |
|---|---|---|
| `text` | CharField (document) | Full-text: name, uniquename, dbxrefs, GO terms, protein matches, annotations, DOIs, expression samples, overlapping features |
| `autocomplete` | EdgeNgramField | Organism + text for typeahead |
| `organism` | CharField (faceted) | `{genus} {species} [{infraspecific}]` |
| `so_term` | CharField (faceted) | Sequence Ontology type name |
| `uniquename` | CharField (faceted) | Feature unique identifier |
| `name` | CharField (faceted) | Feature display name |
| `analyses` | MultiValueField (faceted) | BLAST/InterProScan/Diamond match status |
| `display` | CharField (faceted) | Display text (product/description/note) |
| `doi` | MultiValueField (faceted) | Publication DOIs |
| `relationship` | MultiValueField | Related feature IDs and types |
| `biomaterial` | MultiValueField (faceted) | RNA-seq biomaterial descriptions |
| `treatment` | MultiValueField (faceted) | RNA-seq treatment names |
| `orthology` | BooleanField (faceted) | Has orthologous group (conditional) |
| `orthologous_group` | CharField (faceted) | Orthologous group ID (conditional) |
| `coexpression` | BooleanField (faceted) | Has coexpression group (conditional) |
| `coexpression_group` | CharField (faceted) | Coexpression group ID (conditional) |

**Index queryset filter:** Only features matching `MACHADO_VALID_TYPES` setting with `cv.name = 'sequence'` and `is_obsolete = False`.

### 8.2 Search Form (`forms.py`)

`FeatureSearchForm` extends Haystack's `FacetedSearchForm`:
- Union (OR) logic for most facets
- Intersection (AND) logic for `analyses` facet
- Escapes special characters (`:`, `/`, `.`, `"`) for Elasticsearch compatibility

### 8.3 Faceted Search View

12 facet categories with configurable ordering, pagination (default 50), and sort direction toggle. Export to TSV or FASTA format.

---

## 9. Web Interface

### 9.1 Templates

| Template | Route | Description |
|---|---|---|
| `base.html` | — | Base layout (extends all pages) |
| `index.html` | `/` | Home page |
| `congrats.html` | `/` (no haystack) | Setup confirmation with data counts |
| `data-numbers.html` | `/data/` | Data summary per organism |
| `feature.html` | `/feature/?feature_id=X` | Feature detail page |
| `search_result.html` | `/find/` | Faceted search results |
| `search_form.html` | — | Search input partial |
| `search_facet.html` | — | Facet sidebar partial |
| `search_result.out` | `/export/` | TSV/FASTA export |
| `error.html` | — | Error display |

### 9.2 Template Tags (`machado_extras.py`)

- `param_replace` — URL parameter manipulation for pagination/sorting/facets
- `remove_query` — clear search query
- `remove_facet` — remove specific facet selection
- `remove_facet_field` — remove entire facet category
- `get_item`, `get_count` — dictionary helpers
- `split` — string split filter

### 9.3 JavaScript

- `feature.js` (9.5 KB) — Feature detail page interactivity
- `main.js` (857 B) — General page functionality

---

## 10. Configuration

### 10.1 Auto-Patching (`machado/settings.py`)

On app startup (`MachadoConfig.ready()`), Machado automatically patches Django settings:

- **Middleware:** Adds session, auth, and messages middleware
- **URL routing:** Merges machado URLs into `ROOT_URLCONF`
- **Templates:** Configures Django template backend if empty
- **Swagger:** Sets `USE_SESSION_AUTH = False`
- **Proxy:** Enables `X-Forwarded-Host` and SSL proxy headers
- **Formatting:** Enables thousand separators, appends slashes

### 10.2 Required Settings

| Setting | Type | Description |
|---|---|---|
| `MACHADO_VALID_TYPES` | list[str] | SO terms to index (e.g., `["gene", "mRNA", "polypeptide"]`) |

### 10.3 Optional Settings

| Setting | Type | Default | Description |
|---|---|---|---|
| `CACHE_TIMEOUT` | int | 3600 | View cache duration in seconds |
| `MACHADO_JBROWSE_URL` | str | — | JBrowse instance base URL |
| `MACHADO_JBROWSE_TRACKS` | str | `"ref_seq,gene,transcripts,CDS"` | Default visible tracks |
| `MACHADO_JBROWSE_OFFSET` | int | 1000 | Base pairs padding for JBrowse view |
| `MACHADO_URL` | str | — | Public base URL for Swagger docs |

### 10.4 Database Configuration

Requires PostgreSQL with Chado schema pre-installed:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'yourdatabase',
        'USER': 'username',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### 10.5 Elasticsearch Configuration

```python
HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.elasticsearch7_backend.Elasticsearch7SearchEngine',
        'URL': 'http://127.0.0.1:9200/',
        'INDEX_NAME': 'haystack',
    },
}
```

---

## 11. Testing

### 11.1 Test Suite (`machado/tests/`)

22 test files covering all major subsystems:

| Test File | Coverage Area |
|---|---|
| `test_loaders_ontology.py` | Ontology import (OBO parsing) |
| `test_loaders_feature.py` | Feature loading (GFF, VCF, annotations) |
| `test_loaders_similarity.py` | BLAST/InterProScan import |
| `test_loaders_orthology.py` | Orthology group loading |
| `test_loaders_coexpression.py` | Co-expression data |
| `test_loaders_sequence.py` | FASTA sequence import |
| `test_loaders_organism.py` | Organism management |
| `test_loaders_publication.py` | BibTeX import |
| `test_loaders_analysis.py` | Analysis records |
| `test_loaders_common.py` | Common utilities |
| `test_loaders_featureattributes.py` | GFF attribute parsing |
| `test_loaders_biomaterial.py` | Biomaterial records |
| `test_loaders_assay.py` | Assay records |
| `test_loaders_phylotree.py` | Phylogenetic trees |
| `test_loaders_project.py` | Project records |
| `test_loaders_treatment.py` | Treatment records |
| `test_models.py` | Model decorator methods |
| `test_views_common.py` | Common web views |
| `test_views_feature.py` | Feature detail views |
| `test_templatetags.py` | Template tag functions |

### 11.2 Test Configuration

Dedicated settings at `machado/tests/settings.py` with PostgreSQL service.

### 11.3 Running Tests

```bash
python manage.py test machado --settings machado.tests.settings
```

### 11.4 Coverage

Configured in `.coveragerc` — branch coverage enabled, excludes `bin/`, `docs/`, `extras/`, `migrations/`, `schemas/`, `static/`, `tests/`, `management/`.

---

## 12. CI/CD Pipeline

**File:** `.github/workflows/django.yml`

- **Triggers:** Push/PR to `master`
- **Matrix:** Python 3.10/3.11/3.12 × Ubuntu 22.04/24.04
- **Services:** PostgreSQL 15 container
- **Steps:**
  1. Install package (`pip install -e .`)
  2. Lint with flake8 + flake8-black
  3. Create Django project (`django-admin startproject WEBPROJECT`)
  4. Run test suite

---

## 13. Utilities

### 13.1 `bin/fixChadoModel.py`

Post-processing script for `python manage.py inspectdb` output:
- Adds explicit `related_name` to all ForeignKey fields
- Removes `managed = False` lines
- Generates corresponding `admin.py` with model registrations

### 13.2 Coding Standards

- **Style:** PEP 8 + PEP 257
- **Linter:** flake8 with suppressed rules: `E501` (line length), `W503`, `D100/D101/D104/D106` (missing docstrings for modules/classes/packages)
- **All contributions** must include tests and pass CI

---

## 14. Deployment

### 14.1 Installation

```bash
pip install -e .
```

### 14.2 Docker

Pre-built Docker setup available: https://github.com/lmb-embrapa/machado-docker

### 14.3 Prerequisites

1. PostgreSQL with Chado schema loaded (`schemas/1.31/default_schema.sql`)
2. Elasticsearch 7.17 running
3. Django project with `machado` in `INSTALLED_APPS`
4. `MACHADO_VALID_TYPES` configured

---

## 15. Contributors

- Adhemar Zerlotini (https://github.com/azneto)
- Maurício de A. Mudadu (https://github.com/mmudado)
- Nick Booher (https://github.com/njbooher)
- Instituto Federal de Educação, Ciência e Tecnologia de São Paulo — IFSP
