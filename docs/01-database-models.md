# Database Layer — Chado ORM Models

> **Source file:** `machado/models.py` (4,350 lines)  
> **Schema version:** Chado 1.31  
> **Schema SQL:** `machado/schemas/1.31/default_schema.sql`

---

## Architecture

All models use `managed = False` — they map to pre-existing PostgreSQL Chado tables. Machado does **not** create or migrate database tables through Django migrations. The Chado schema must be pre-installed in the PostgreSQL database.

### Conventions

- **Primary keys:** `BigAutoField` on every model
- **Foreign keys:** `on_delete=models.DO_NOTHING` (database handles referential integrity)
- **Related names:** Follow the pattern `{ModelName}_{field}_{TargetModel}` (e.g., `Feature_organism_Organism`)
- **Model maintenance:** The `bin/fixChadoModel.py` script post-processes `inspectdb` output to add `related_name` attributes

---

## Model Groups

### Controlled Vocabulary (CV)

| Model | Table | Description |
|---|---|---|
| `Cv` | `cv` | Controlled vocabulary namespace (e.g., "sequence", "relationship") |
| `Cvterm` | `cvterm` | Individual terms within a CV. Unique on `(name, cv, is_obsolete)` |
| `CvtermRelationship` | `cvterm_relationship` | Typed relationships between CV terms (is_a, part_of, etc.) |
| `CvtermDbxref` | `cvterm_dbxref` | Cross-references for CV terms |
| `Cvtermsynonym` | `cvtermsynonym` | Synonyms for CV terms. Unique on `(cvterm, synonym)` |
| `Cvtermprop` | `cvtermprop` | Properties/metadata for CV terms |
| `Cvtermpath` | `cvtermpath` | Transitive closure paths in ontology graphs |
| `Cvprop` | `cvprop` | Properties of controlled vocabularies |

### Database Cross-References

| Model | Table | Description |
|---|---|---|
| `Db` | `db` | External database registry (e.g., "GO", "DOI", "FASTA_SOURCE") |
| `Dbxref` | `dbxref` | Accession in an external database. Unique on `(db, accession, version)` |
| `Dbxrefprop` | `dbxrefprop` | Properties for cross-references |
| `Dbprop` | `dbprop` | Properties for databases |

### Organism

| Model | Table | Description |
|---|---|---|
| `Organism` | `organism` | Species/strain. Unique on `(genus, species, type, infraspecific_name)` |
| `OrganismDbxref` | `organism_dbxref` | External refs (e.g., NCBI Taxonomy ID) |
| `Organismprop` | `organismprop` | Properties (synonyms, etc.) |
| `OrganismPub` | `organism_pub` | Publication links |

### Sequence / Feature (Core)

The `Feature` model is the central entity of Machado:

| Model | Table | Description |
|---|---|---|
| `Feature` | `feature` | Any biological feature (gene, mRNA, polypeptide, chromosome, etc.) |
| `Featureloc` | `featureloc` | Genomic coordinates (fmin, fmax, strand, phase) with source feature |
| `FeatureRelationship` | `feature_relationship` | Typed relationships between features (part_of, translation_of) |
| `FeatureRelationshipprop` | `feature_relationshipprop` | Properties on relationships |
| `Featureprop` | `featureprop` | Arbitrary key-value properties (display, product, description, etc.) |
| `FeaturepropPub` | `featureprop_pub` | Publication links on properties |
| `FeatureCvterm` | `feature_cvterm` | Ontology term associations (GO terms, etc.) |
| `FeatureCvtermprop` | `feature_cvtermprop` | Properties on feature-cvterm associations |
| `FeatureDbxref` | `feature_dbxref` | External database cross-references for features |
| `FeaturePub` | `feature_pub` | Publication links for features |
| `FeatureSynonym` | `feature_synonym` | Synonyms/aliases for features |
| `FeatureGenotype` | `feature_genotype` | Genotype associations |
| `FeaturePhenotype` | `feature_phenotype` | Phenotype associations |

**Feature model key fields:**

```python
class Feature(models.Model):
    feature_id     = BigAutoField(primary_key=True)
    dbxref         = ForeignKey(Dbxref)        # unique accession
    organism       = ForeignKey(Organism)       # species
    name           = CharField(max_length=255)  # display name
    uniquename     = TextField()                # unique identifier
    residues       = TextField()                # sequence data
    seqlen         = IntegerField()             # sequence length
    md5checksum    = CharField(max_length=32)   # sequence checksum
    type           = ForeignKey(Cvterm)          # SO term (gene, mRNA, etc.)
    is_analysis    = BooleanField()             # computational result flag
    is_obsolete    = BooleanField()             # obsolescence flag
    timeaccessioned = DateTimeField()
    timelastmodified = DateTimeField()
```

### Analysis

| Model | Table | Description |
|---|---|---|
| `Analysis` | `analysis` | Computational analysis (BLAST, InterProScan, Diamond) |
| `Analysisfeature` | `analysisfeature` | Links analysis to features with scores (rawscore, normscore, significance, identity) |
| `Analysisprop` | `analysisprop` | Analysis properties |
| `AnalysisRelationship` | `analysis_relationship` | Relationships between analyses |

### Publication

| Model | Table | Description |
|---|---|---|
| `Pub` | `pub` | Publication record (title, year, journal, volume, pages) |
| `PubDbxref` | `pub_dbxref` | External references (DOI) |
| `Pubauthor` | `pubauthor` | Author records with rank ordering |
| `Pubprop` | `pubprop` | Publication properties |
| `PubRelationship` | `pub_relationship` | Relationships between publications |

### Phylogeny

| Model | Table | Description |
|---|---|---|
| `Phylotree` | `phylotree` | Phylogenetic tree metadata |
| `Phylonode` | `phylonode` | Individual nodes in a phylogenetic tree |
| `PhylonodeRelationship` | `phylonode_relationship` | Parent-child relationships between nodes |

### Expression / Microarray

| Model | Table | Description |
|---|---|---|
| `Assay` | `assay` | Experimental assay (RNA-seq experiment) |
| `AssayBiomaterial` | `assay_biomaterial` | Links assays to biomaterials |
| `Biomaterial` | `biomaterial` | Biological sample |
| `Biomaterialprop` | `biomaterialprop` | Sample properties |
| `BiomaterialRelationship` | `biomaterial_relationship` | Relationships between samples |
| `Acquisition` | `acquisition` | Data acquisition from assay |
| `Quantification` | `quantification` | Quantification of acquisition data |
| `Treatment` | `treatment` | Experimental treatment applied to biomaterial |

### Stock / Natural Diversity

| Model | Table | Description |
|---|---|---|
| `Stock` | `stock` | Germplasm/stock record |
| `Stockprop` | `stockprop` | Stock properties |
| `NdExperiment` | `nd_experiment` | Natural diversity experiment |
| `NdGeolocation` | `nd_geolocation` | Geographic location for experiments |

### Genotype / Phenotype

| Model | Table | Description |
|---|---|---|
| `Genotype` | `genotype` | Genotype record |
| `Phenotype` | `phenotype` | Phenotype record with observable/attribute/value |
| `FeatureGenotype` | `feature_genotype` | Links features to genotypes |
| `FeaturePhenotype` | `feature_phenotype` | Links features to phenotypes |

---

## Decorator-Injected Methods

The `machado/decorators.py` module dynamically attaches methods to models at import time:

### Feature Methods (`@machado_feature_methods`)

| Method | Return Type | Description |
|---|---|---|
| `get_display()` | `str \| None` | Priority chain: display → product → description → note |
| `get_product()` | `str \| None` | Product annotation from featureprop |
| `get_description()` | `str \| None` | Description from featureprop |
| `get_note()` | `str \| None` | Note from featureprop |
| `get_annotation()` | `list[dict]` | All annotation values with optional DOI references |
| `get_doi()` | `list[str]` | Publication DOIs linked to the feature |
| `get_dbxrefs()` | `list[dict]` | External DB cross-refs with URL prefix |
| `get_orthologous_group()` | `str \| None` | Orthologous group ID |
| `get_coexpression_group()` | `str \| None` | Co-expression group ID |
| `get_expression_samples()` | `QuerySet` | RNA-seq expression values with biomaterial/treatment metadata |
| `get_relationship()` | `QuerySet` | Related features (parents/children via part_of, translation_of) |
| `get_cvterm()` | `QuerySet` | Associated ontology terms |
| `get_location()` | `list[dict]` | Genomic coordinates with JBrowse URL generation |
| `get_properties()` | `dict` | All featureprop key-value pairs |
| `get_synonyms()` | `list[str]` | Feature synonyms |

### Pub Methods (`@machado_pub_methods`)

| Method | Return Type | Description |
|---|---|---|
| `get_authors()` | `str` | Formatted author string (surname1, surname2, and surname3) |
| `get_doi()` | `str \| None` | DOI accession for the publication |

---

## History Model

Machado includes a managed `History` model (the only managed model) for tracking data loading operations:

```python
class History(models.Model):
    history_id  = BigAutoField(primary_key=True)
    command     = CharField(max_length=255)    # management command name
    params      = TextField()                  # command parameters
    description = TextField()                  # human-readable description
    created_at  = DateTimeField(auto_now_add=True)
    finished_at = DateTimeField(null=True)
    exit_code   = IntegerField(default=-1)

    class Meta:
        managed = True
        db_table = "history"
```
