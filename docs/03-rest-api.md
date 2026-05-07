# REST API — Comprehensive Reference

> **Source files:**  
> - `machado/api/urls.py` — Route definitions  
> - `machado/api/views/read.py` — Read-only ViewSets (1,036 lines)  
> - `machado/api/views/load.py` — Data ingestion ViewSets (38 KB)  
> - `machado/api/serializers/read.py` — Read serializers (550 lines)  
> - `machado/api/serializers/load.py` — Load serializers  
> - `machado/account/views.py` — Authentication ViewSets

---

## Architecture

- **Framework:** Django REST Framework (DRF) 3.15.x
- **Router:** `SimpleRouter` with `DefaultRouter` for load endpoints
- **Nested routes:** `drf-nested-routers` for JBrowse feature paths
- **API docs:** drf-yasg (Swagger/OpenAPI) at `/api/`
- **Caching:** `@cache_page(CACHE_TIMEOUT)` on all read endpoints (default: 3600s)
- **Pagination:** `StandardResultSetPagination` — 100 items/page, max 1000

---

## JBrowse REST API

Machado serves as a REST data backend for the JBrowse genome browser, implementing the [JBrowse REST API](https://jbrowse.org/docs/data_formats.html).

### `GET /api/jbrowse/stats/global`

Returns global statistics for JBrowse.

**Response:**
```json
[{"featureDensity": 0.02}]
```

---

### `GET /api/jbrowse/refSeqs.json`

Returns reference sequences for JBrowse initialization.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `organism` | string | yes | Species name (e.g., "Arabidopsis thaliana") |
| `soType` | string | yes | SO term (e.g., "chromosome") |

**Response:**
```json
[
  {"name": "Chr1", "start": 1, "end": 30427671},
  {"name": "Chr2", "start": 1, "end": 19698289}
]
```

---

### `GET /api/jbrowse/names`

Searches features by name/accession for JBrowse name store.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `organism` | string | yes | Species name |
| `equals` | string | no | Exact match on uniquename |
| `startswith` | string | no | Prefix match on uniquename |

**Response:**
```json
[
  {
    "name": "AT1G01010",
    "location": {
      "ref": "Chr1", "start": 3631, "end": 5899,
      "type": "gene", "tracks": [], "objectName": "AT1G01010"
    }
  }
]
```

---

### `GET /api/jbrowse/features/{refseq}`

Returns features overlapping a genomic region for JBrowse track display.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `organism` | string | yes | Species name |
| `soType` | string | no | SO term filter (gene, mRNA, CDS, etc.) |
| `start` | integer | no | Region start (default: 1) |
| `end` | integer | no | Region end |

**Response:**
```json
{
  "features": [
    {
      "uniqueID": "AT1G01010",
      "accession": "AT1G01010",
      "name": "NAC001",
      "type": "gene",
      "start": 3631,
      "end": 5899,
      "strand": 1,
      "seq": null,
      "display": "NAC domain containing protein 1",
      "subfeatures": [
        {"type": "exon", "start": 3631, "end": 3913, "strand": 1, "phase": null}
      ]
    }
  ]
}
```

**Serializer details (`JBrowseFeatureSerializer`):**
- `subfeatures` — retrieves child features via `part_of` relationships
- `display` — calls `Feature.get_display()` decorator method
- `seq` — returns `Feature.residues` (nucleotide/protein sequence)
- `start`/`end` — computed from `Featureloc` relative to refseq context

---

## Search API

### `GET /api/autocomplete`

Provides typeahead search suggestions from the Elasticsearch index.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `q` | string | yes | Search query |

**Behavior:**
- Queries Haystack `SearchQuerySet` with EdgeNgram `autocomplete` field
- Returns up to 10 unique matches
- Extracts matching words using regex against the autocomplete field

**Response:**
```json
["Arabidopsis thaliana gene1", "Arabidopsis thaliana gene2"]
```

---

## Organism API

### `GET /api/organism/id`

Retrieve organism ID by attributes.

| Parameter | Type | Required |
|---|---|---|
| `genus` | string | no |
| `species` | string | no |
| `infraspecific_name` | string | no |
| `abbreviation` | string | no |
| `common_name` | string | no |

**Response:** `{"organism_id": 1}`

---

### `GET /api/organism/list`

Returns all organisms (excludes "multispecies" placeholder).

**Response:**
```json
[
  {
    "organism_id": 1,
    "genus": "Arabidopsis",
    "species": "thaliana",
    "abbreviation": "A. thaliana",
    "common_name": "thale cress",
    "infraspecific_name": null,
    "comment": null
  }
]
```

---

## Feature API

### `GET /api/feature/id`

Retrieve feature ID by accession.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `accession` | string | yes | Feature name or accession |
| `soType` | string | yes | SO term |
| `organism_id` | integer | yes | Organism ID |

**Response:** `{"feature_id": 12345}`

---

### `GET /api/feature/info/{feature_id}`

Comprehensive feature information.

**Response:**
```json
{
  "uniquename": "AT1G01010.1",
  "display": "NAC domain containing protein 1",
  "product": "transcription factor",
  "note": "NAC family",
  "organism": "Arabidopsis thaliana",
  "relationship": [
    {
      "relative_feature_id": 100,
      "relative_type": "gene",
      "relative_uniquename": "AT1G01010",
      "relative_display": "NAC domain containing protein 1"
    }
  ],
  "dbxref": [
    {"db": "UniProt", "accession": "Q0WVJ4", "url": "https://..."}
  ]
}
```

---

### `GET /api/feature/location/{feature_id}`

Genomic coordinates with JBrowse link.

**Response:**
```json
[
  {
    "start": 3631,
    "end": 5899,
    "strand": 1,
    "ref": "Chr1",
    "jbrowse_url": "https://jbrowse.example.com/?loc=Chr1:2631..6899&tracks=ref_seq,gene,transcripts,CDS"
  }
]
```

---

### `GET /api/feature/ontology/{feature_id}`

Ontology terms associated with the feature.

**Response:**
```json
[
  {
    "cvterm": "DNA binding",
    "cvterm_definition": "Any molecular function by which...",
    "cv": "molecular_function",
    "db": "GO",
    "dbxref": "0003677"
  }
]
```

---

### `GET /api/feature/ortholog/{feature_id}`

Orthologous group members.

**Response:**
```json
{
  "ortholog_group": "OG0001234",
  "members": [
    {
      "feature_id": 456,
      "uniquename": "Os01g01010.1",
      "display": "hypothetical protein",
      "organism": "Oryza sativa"
    }
  ]
}
```

---

### `GET /api/feature/coexpression/{feature_id}`

Co-expression group members (same response structure as ortholog).

---

### `GET /api/feature/expression/{feature_id}`

RNA-seq expression values across samples.

**Response:**
```json
[
  {
    "analysis__sourcename": "rnaseq_sample1.tsv",
    "normscore": 42.5,
    "assay_name": "RNA-seq Experiment 1",
    "assay_description": "Leaf tissue",
    "biomaterial_name": "Sample_A",
    "biomaterial_description": "Leaf tissue, 3 weeks",
    "treatment_name": "Control"
  }
]
```

---

### `GET /api/feature/proteinmatches/{feature_id}`

Protein domain matches from InterProScan/BLAST.

**Response:**
```json
[
  {
    "subject_id": "PF00847",
    "subject_desc": "NAC domain",
    "db": "PFAM",
    "dbxref": "PF00847"
  }
]
```

---

### `GET /api/feature/similarity/{feature_id}`

Similarity search results (BLAST/Diamond).

**Response:**
```json
[
  {
    "program": "blastp",
    "programversion": "2.12.0",
    "db_name": "UniProt",
    "unique": "Q0WVJ4",
    "name": "NAC1_ARATH",
    "sotype": "polypeptide",
    "query_start": "1",
    "query_end": "324",
    "score": "625",
    "evalue": "1e-180"
  }
]
```

---

### `GET /api/feature/publication/{feature_id}`

Publications linked to the feature.

**Response:**
```json
[
  {
    "doi": "10.1234/example",
    "authors": "Smith, Jones, and Brown",
    "title": "Genome-wide analysis...",
    "series_name": "Nature Genetics",
    "pyear": "2020",
    "volume": "52",
    "pages": "100-110"
  }
]
```

---

### `GET /api/feature/sequence/{feature_id}`

Feature nucleotide/protein sequence.

**Response:** `{"sequence": "ATGCGATCGATCG..."}`

---

## History API

### `GET /api/history`

Returns data loading history.

**Response:**
```json
[
  {
    "history_id": 1,
    "command": "load_fasta",
    "params": {"genus": "Arabidopsis", "species": "thaliana", ...},
    "description": "Loading FASTA file",
    "created_at": "2024-01-15T10:30:00Z",
    "finished_at": "2024-01-15T10:35:00Z",
    "exit_code": 0
  }
]
```

---

## Data Loading API

All load endpoints accept POST requests and mirror the CLI management commands:

| Endpoint | Method | Description |
|---|---|---|
| `POST /api/load/organism` | POST | Create organism (genus, species, infraspecific_name, etc.) |
| `POST /api/load/relations_ontology` | POST | Load RO from OBO file |
| `POST /api/load/sequence_ontology` | POST | Load SO from OBO file |
| `POST /api/load/gene_ontology` | POST | Load GO from OBO file |
| `POST /api/load/publication` | POST | Load BibTeX publication |
| `POST /api/load/fasta` | POST | Load FASTA sequences |
| `POST /api/load/gff` | POST | Load GFF3 features |
| `POST /api/load/feature_annotation` | POST | Load feature annotations |
| `POST /api/load/feature_sequence` | POST | Load feature sequences |
| `POST /api/load/feature_dbxrefs` | POST | Load feature cross-references |
| `POST /api/load/feature_publication` | POST | Link features to publications |

---

## Authentication API

Token-based authentication using DRF's `TokenAuthentication`.

### `POST /account/login`

| Field | Type | Required |
|---|---|---|
| `email` | string | yes |
| `password` | string | yes |

**Response:** `{"token": "abc123...", "user_id": 1, "email": "user@example.com"}`

### `POST /account/logout`

Requires `Authorization: Token <token>` header. Deletes the token.

### `GET /account/` (Admin only)

List all users. Returns: `id`, `username`, `email`, `first_name`, `last_name`, `is_staff`.

### `POST /account/` (Admin only)

Create user. Fields: `username`, `email`, `password`, `first_name`, `last_name`, `is_staff`.
Validates unique username and email.

### `GET /account/{id}` | `PUT /account/{id}` | `DELETE /account/{id}` (Admin only)

CRUD operations on individual users.

### `GET /account/username/{username}` (Admin only)

Search user by username.
