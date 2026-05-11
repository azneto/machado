# Testing & CI/CD

> **Source files:**  
> - `machado/tests/` — 22 test files  
> - `machado/tests/settings.py` — Test configuration  
> - `.github/workflows/django.yml` — CI pipeline  
> - `.coveragerc` — Coverage configuration  
> - `.flake8` — Linting rules

---

## Test Suite

### Test Configuration (`tests/settings.py`)

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

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'machado',
]
```

### Running Tests

```bash
# Run all tests
python manage.py test machado --settings machado.tests.settings

# Run specific test module
python manage.py test machado.tests.test_loaders_feature --settings machado.tests.settings

# Run with verbosity
python manage.py test machado --settings machado.tests.settings -v 2
```

---

## Test Files — Detailed Reference

### Loader Tests

| Test File | Size | Coverage Target |
|---|---|---|
| `test_loaders_ontology.py` | 15 KB | OBO parsing, term storage, relationships, synonyms, xrefs |
| `test_loaders_feature.py` | 28 KB | GFF3 feature loading, VCF variants, annotations, dbxrefs, publications, relationships |
| `test_loaders_similarity.py` | 14 KB | BLAST-XML and InterProScan-XML import, match_part creation, GO term propagation |
| `test_loaders_orthology.py` | 23 KB | OrthoMCL group loading, single and multi-species modes |
| `test_loaders_coexpression.py` | 16 KB | Co-expression cluster and pair loading |
| `test_loaders_sequence.py` | 8 KB | FASTA import, duplicate detection, MD5 checksums |
| `test_loaders_organism.py` | 4 KB | Organism creation, scientific name parsing, publications |
| `test_loaders_publication.py` | 3 KB | BibTeX parsing, author extraction, DOI storage |
| `test_loaders_analysis.py` | 12 KB | Analysis record creation, analysisfeature management |
| `test_loaders_common.py` | 4 KB | File validation, feature retrieval strategies |
| `test_loaders_featureattributes.py` | 6 KB | GFF attribute parsing, ontology terms, dbxrefs, synonyms |
| `test_loaders_biomaterial.py` | 4 KB | Biomaterial record creation |
| `test_loaders_assay.py` | 4 KB | Assay, acquisition, quantification records |
| `test_loaders_phylotree.py` | 4 KB | Newick tree parsing, phylonode creation |
| `test_loaders_project.py` | 2 KB | Project record creation |
| `test_loaders_treatment.py` | 1 KB | Treatment record creation |

### Model Tests

| Test File | Size | Coverage Target |
|---|---|---|
| `test_models.py` | 3 KB | Decorator-injected methods: `get_display()`, `get_relationship()`, `get_location()`, etc. |

### View Tests

| Test File | Size | Coverage Target |
|---|---|---|
| `test_views_common.py` | 10 KB | Home page, data summary, status codes, context data |
| `test_views_feature.py` | 13 KB | Feature detail page, presence flags, error handling |

### Template Tag Tests

| Test File | Size | Coverage Target |
|---|---|---|
| `test_templatetags.py` | 2 KB | `param_replace`, `remove_query`, `remove_facet`, `remove_facet_field` |

### Test Data

The `machado/tests/data/` directory contains sample input files used by tests:
- OBO ontology snippets
- GFF3 feature files
- FASTA sequence files
- BLAST-XML output
- InterProScan-XML output
- BibTeX entries
- VCF variant files
- TSV annotation files

---

## Coverage Configuration (`.coveragerc`)

```ini
[run]
branch = True
source = machado

[report]
omit =
    bin/*
    docs/*
    extras/*
    machado/migrations/*
    machado/schemas/*
    machado/static/*
    machado/tests/*
    machado/management/*
```

**Key points:**
- Branch coverage enabled
- Excludes: migrations, schema SQL, static assets, tests, management commands
- Focuses coverage on: models, decorators, loaders, views, API, forms, search indexes

---

## CI/CD Pipeline (`.github/workflows/django.yml`)

### Trigger Events

```yaml
on:
  push:
    branches: ["master"]
  pull_request:
    branches: ["master"]
```

### Test Matrix

| Dimension | Values |
|---|---|
| Python | 3.10, 3.11, 3.12 |
| OS | Ubuntu 22.04, Ubuntu 24.04 |
| Max parallel | 4 |

### Services

```yaml
services:
  postgres:
    image: postgres:15
    env:
      POSTGRES_USER: username
      POSTGRES_PASSWORD: password
      POSTGRES_DB: yourdatabase
    ports:
      - 5432:5432
    options: --health-cmd pg_isready --health-interval 10s --health-timeout 5s --health-retries 5
```

### Pipeline Steps

1. **Checkout** — `actions/checkout@v3`
2. **Python setup** — `actions/setup-python@v3`
3. **Install dependencies** — `pip install -e .`
4. **Lint** — `flake8 machado` (with `flake8-black`)
5. **Create project** — `django-admin startproject WEBPROJECT`
6. **Run tests** — `python WEBPROJECT/manage.py test machado --settings machado.tests.settings`

---

## Linting Configuration (`.flake8`)

```ini
[flake8]
max-line-length = 100
extend-ignore =
    E501   # line too long (handled by Black)
    W503   # line break before binary operator
    D100   # missing docstring in public module
    D101   # missing docstring in public class
    D104   # missing docstring in public package
    D106   # missing docstring in public nested class
```

### Code Style Requirements

- **Formatter:** Black (enforced via `flake8-black`)
- **Docstrings:** PEP 257 (required for functions/methods, optional for modules/classes)
- **Max line length:** 100 characters (flexible via Black)

---

## Contributing

### Pull Request Template (`.github/PULL_REQUEST_TEMPLATE.md`)

Requirements:
1. Reference the issue being addressed
2. Agree to GPLv3 license
3. Pass CI (tests + flake8)
4. Optionally add name to `CONTRIB.rst`

### Issue Template (`.github/ISSUE_TEMPLATE.md`)

Required information:
- Python version and platform
- Expected behavior
- Actual behavior

---

## Deployment & Configuration

### Required Settings for Machado

```python
# settings.py
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'drf_yasg',
    'machado',
]

# Database (PostgreSQL with Chado schema)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'your_chado_database',
        'USER': 'your_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}



# Machado-specific settings
MACHADO_VALID_TYPES = ['gene', 'mRNA', 'polypeptide']

# Optional
CACHE_TIMEOUT = 3600
MACHADO_JBROWSE_URL = 'https://your-jbrowse-instance.com'
MACHADO_JBROWSE_TRACKS = 'ref_seq,gene,transcripts,CDS'
MACHADO_JBROWSE_OFFSET = 1000
```

### JBrowse Integration

Sample track configuration in `extras/trackList.json.sample`:
- Reference sequence track (REST store)
- Gene track (CanvasFeatures)
- Transcript track (CanvasFeatures)
- CDS track (CanvasFeatures)
- SNV track (HTMLFeatures)

All tracks use `JBrowse/Store/SeqFeature/REST` store class pointing to Machado's API.

### Docker Deployment

Pre-built Docker environment: https://github.com/lmb-embrapa/machado-docker

### Installation from Source

```bash
git clone https://github.com/lmb-embrapa/machado.git
cd machado
pip install -e .
```

### Database Setup

```bash
# Install Chado schema
psql -d your_database -f machado/schemas/1.31/default_schema.sql

# Create Django tables (only History model is managed)
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### Utilities

#### `bin/fixChadoModel.py`

Post-processes `python manage.py inspectdb` output:

```bash
python manage.py inspectdb > models_raw.py
python bin/fixChadoModel.py models_raw.py machado/models.py machado/admin.py
```

**Actions:**
- Adds `related_name` to all ForeignKey fields following `{ModelName}_{field}_{TargetModel}` pattern
- Removes `managed = False` from output (must be manually re-added)
- Generates `admin.py` with `admin.site.register()` calls for all models
