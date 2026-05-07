# Data Loaders — Comprehensive Reference

> **Source directory:** `machado/loaders/` (16 modules)  
> **CLI commands:** `machado/management/commands/` (33 commands)

---

## Loader Library Architecture

All loaders follow a consistent pattern:
1. **Initialization** — validate inputs, retrieve CV terms, set up DB/Dbxref records
2. **Store methods** — create Django ORM objects for the target data
3. **Error handling** — raise `ImportingError` for all import failures

### Common Utilities (`loaders/common.py`)

| Class/Function | Purpose |
|---|---|
| `FileValidator` | Validates file existence and extension |
| `FieldsValidator` | Validates required column count in TSV files |
| `retrieve_organism(name)` | Looks up `Organism` by `"{genus} {species}"` string |
| `retrieve_feature_id(accession, soterm, organism)` | Multi-strategy feature lookup: uniquename → soterm-uniquename → name → dbxref → feature_dbxref |
| `retrieve_cvterm(cv, term)` | Retrieves `Cvterm` by CV name and term name |

### Exceptions (`loaders/exceptions.py`)

Single exception class: `ImportingError(Exception)` — used across all loaders.

---

## Loader Modules — Detailed Reference

### OntologyLoader (`loaders/ontology.py`)

**Purpose:** Load OBO-format ontologies (SO, GO, RO) into the Chado CV system.

**Class:** `OntologyLoader(cv_name, cv_definition=None)`

**Methods:**

| Method | Description |
|---|---|
| `store_type_def(typedef)` | Store ontology typedef (relationship types like `is_a`, `part_of`) |
| `store_term(n, data, lock=None)` | Store individual ontology term with definition, alt_ids, comments, xrefs, synonyms |
| `store_relationship(u, v, type)` | Store `is_a` or other typed relationships between terms |
| `process_cvterm_def(cvterm, definition)` | Parse `"text" [DB:accession]` format definitions |
| `process_cvterm_xref(cvterm, xref)` | Store cross-references for terms |
| `process_cvterm_go_synonym(cvterm, synonym, type)` | Parse GO-style synonyms (`"text" [DB:ref]`) |
| `process_cvterm_so_synonym(cvterm, synonym)` | Parse SO-style synonyms (`"text" TYPE []`) |

**Initialization creates:**
- `_global`, `internal`, `OBO_REL` databases
- `cvterm_property_type`, `relationship`, `synonym_type` CVs
- Meta-terms: `is_symmetric`, `is_transitive`, `is_class_level`, `is_metadata_tag`, `comment`, `is_a`

---

### SequenceLoader (`loaders/sequence.py`)

**Purpose:** Load FASTA sequences as `Feature` records.

**Class:** `SequenceLoader(filename, organism, doi=None, description=None, url=None)`

**Methods:**

| Method | Parameters | Description |
|---|---|---|
| `store_biopython_seq_record(seq_obj, soterm, ignore_residues=False)` | BioPython SeqRecord | Creates Feature with residues, seqlen, md5checksum. Database source: `FASTA_SOURCE` |
| `add_sequence_to_feature(seq_obj, soterm)` | BioPython SeqRecord | Attaches sequence to existing feature |

**Key behaviors:**
- Computes MD5 checksum of sequence
- Optionally ignores residues (stores empty string) for large genomes
- Links to publication via DOI if provided
- Prevents duplicate imports (raises `ImportingError`)

---

### FeatureLoader (`loaders/feature.py`)

**Purpose:** Load genomic features from GFF3 and VCF files.

**Classes:**

#### `FeatureLoaderBase(source, filename, doi=None)`
Base class initializing shared resources (null pub, CV terms for `located in`, `polypeptide`, `protein_match`).

#### `FeatureLoader(source, filename, organism, doi=None)` — extends FeatureLoaderBase
Single-organism feature loading.

| Method | Description |
|---|---|
| `store_tabix_GFF_feature(tabix_feature, qtl)` | Store GFF3 features. Handles: ID/Name/Parent parsing, strand conversion (+→1, -→-1), phase handling, auto-ID generation, Featureloc creation, parent relationship tracking. Creates polypeptide records for mRNA/C_gene_segment/V_gene_segment types |
| `store_tabix_VCF_feature(tabix_feature)` | Store VCF variants. Handles: TSA/VC type resolution, quality scores, reference/alternative alleles as multiple Featureloc records |
| `store_relationship(subject_id, object_id)` | Store `part_of` relationship between features |
| `store_feature_annotation(feature, soterm, cvterm, annotation, doi)` | Add annotation property to feature |
| `store_feature_dbxref(feature, soterm, dbxref)` | Add `DB:accession` cross-reference to feature |
| `store_feature_publication(feature, soterm, doi)` | Link feature to publication |
| `store_feature_pairs(pair, term, soterm, value, cache)` | Store pairwise relationships (coexpression pairs) |
| `store_feature_groups(group, term, organism, soterm, value, cache)` | Store group memberships (orthology clusters, coexpression clusters). Only stores groups with ≥2 members |

#### `MultispeciesFeatureLoader(source, filename, doi=None)` — extends FeatureLoaderBase
Cross-organism feature loading (BLAST/InterProScan hits).

| Method | Description |
|---|---|
| `retrieve_feature_id(accession, soterm)` | Multi-strategy lookup without organism constraint |
| `store_bio_searchio_hit(searchio_hit, target)` | Store InterProScan/BLAST hit as protein_match feature. Creates multispecies organism, handles GO terms, dbxrefs |
| `store_feature_groups(group, term, soterm, value, cache)` | Cross-organism group memberships |

---

### FeatureAttributesLoader (`loaders/featureattributes.py`)

**Purpose:** Parse and store GFF3/VCF attributes as feature properties.

**Class:** `FeatureAttributesLoader(filecontent, doi=None)`

**Content types and valid attributes:**

| `filecontent` | Valid Attributes |
|---|---|
| `genome` | dbxref, note, display, alias, ontology_term, orf_classification, synonym, is_circular, gene_synonym, description, product, pacid, doi, freq, cnv_type, annotation |
| `polymorphism` | tsa, vc |
| `qtl` | qtl_id, qtl_type, abbrev, trait, breed, flankmarker, map_type, model, peak_cm, test_base, significance, p-value, trait_id, pubmed_id, doi |

**Attribute processing rules:**

| Attribute | Storage Location | Behavior |
|---|---|---|
| `ontology_term` | `FeatureCvterm` | Resolves `DB:accession` to Cvterm, stores association |
| `dbxref` | `FeatureDbxref` | Parses `DB:accession` format, creates Db + Dbxref |
| `pacid` | `FeatureDbxref` | Stored under `PACID` database |
| `doi` | `FeaturePub` | Links feature to publication via DOI |
| `alias`, `gene_synonym`, `synonym`, `abbrev` | `FeatureSynonym` | Creates Synonym with "exact" type |
| `annotation` | `Featureprop` + `FeaturepropPub` | Supports ranked annotations with DOI links |
| All others | `Featureprop` | Stored as `feature_property` CV terms |

---

### SimilarityLoader (`loaders/similarity.py`)

**Purpose:** Load BLAST and InterProScan search results.

**Class:** `SimilarityLoader(filename, program, programversion, so_query, so_subject, org_query, org_subject, input_format, algorithm=None, name=None, description=None)`

| Method | Description |
|---|---|
| `store_bio_searchio_query_result(query_result)` | Process BioPython SearchIO QueryResult: extract HSPs, create match_part features with Featureloc, Analysisfeature records |
| `store_match_part(query_feature_id, subject_feature_id, identity, rawscore, normscore, significance, query_start, query_end, subject_start, subject_end)` | Create `match_part` feature with two Featureloc records (query and subject) |
| `store_feature_relationship(query_feature_id, subject_feature_id)` | Create similarity relationship, propagate GO terms from subject to query |
| `retrieve_query_from_hsp(hsp)` | Multi-strategy query feature lookup (ID → description ID) |
| `retrieve_subject_from_hsp(hsp)` | Multi-strategy subject feature lookup |

**InterProScan-specific behavior:**
- Creates `in similarity relationship with` feature relationships
- Propagates ontology terms from protein_match to query feature
- For polypeptide queries, also propagates to parent mRNA

---

### OrganismLoader (`loaders/organism.py`)

**Class:** `OrganismLoader(organism_db=None)`

| Method | Description |
|---|---|
| `parse_scientific_name(scname)` | Parse "Genus species [infraspecific]" into tuple |
| `store_organism_record(taxid, scname, synonyms, common_names)` | Create Organism with abbreviation, dbxref, and synonym properties |
| `store_organism_publication(organism, doi)` | Link organism to publication |

---

### PublicationLoader (`loaders/publication.py`)

**Class:** `PublicationLoader()`

| Method | Description |
|---|---|
| `store_bibtex_entry(entry)` | Parse BibTeX entry: creates Pub (title, year, journal, volume, pages), PubDbxref (DOI), and ranked Pubauthor records |

**BibTeX field mapping:**

| BibTeX Field | Pub Field |
|---|---|
| `title` | `title` (strips curly braces) |
| `year` | `pyear` |
| `pages` | `pages` |
| `volume` | `volume` |
| `journal` | `series_name` |
| `ID` | `uniquename` |
| `ENTRYTYPE` | `type` (via Cvterm) |
| `doi` / `DOI` | `PubDbxref` with `db.name = "DOI"` |
| `author` | `Pubauthor` (split on "and", then ",") |

---

### Other Loaders

| Module | Class | Purpose |
|---|---|---|
| `analysis.py` | `AnalysisLoader` | Create/manage Analysis and Analysisfeature records |
| `biomaterial.py` | `BiomaterialLoader` | Create Biomaterial records with Db/Dbxref |
| `assay.py` | `AssayLoader` | Create Assay, Acquisition, Quantification, AssayBiomaterial records |
| `phylotree.py` | `PhylotreeLoader` | Load Newick trees into Phylotree/Phylonode |
| `project.py` | `ProjectLoader` | Create Project records |
| `treatment.py` | `TreatmentLoader` | Create Treatment records linked to Biomaterial |

---

## Management Commands — Detailed Arguments

### Loading Commands

#### `load_relations_ontology`
```
--file    Path to RO OBO file (required)
```

#### `load_sequence_ontology`
```
--file    Path to SO OBO file (required)
```

#### `load_gene_ontology`
```
--file    Path to GO OBO file (required)
--cpu     Number of CPUs for parallel processing (default: 1)
```

#### `insert_organism`
```
--genus              Genus name (required)
--species            Species name (required)
--infraspecific_name  Infraspecific name (optional)
--abbreviation       Abbreviation (optional)
--common_name        Common name (optional)
```

#### `load_organism`
```
--file    TSV file with organism data (required)
--db      Database name for taxonomy IDs (required)
```

#### `load_fasta`
```
--file              FASTA file path (required)
--soterm            SO term: chromosome, scaffold, contig, etc. (required)
--organism          Organism name "Genus species" (required)
--nosequence        Don't store residues (flag)
--doi               Publication DOI (optional)
--description       DB description (optional)
--url               DB URL (optional)
```

#### `load_gff`
```
--file       GFF3 file (bgzipped + tabix-indexed) (required)
--organism   Organism name (required)
--cpu        Number of CPUs (default: 1)
--qtl        Load as QTL features (flag)
--doi        Publication DOI (optional)
```

#### `load_feature_annotation`
```
--file       TSV: feature_accession<TAB>annotation_value (required)
--soterm     SO term of target features (required)
--cvterm     Annotation type: display, product, note, etc. (required)
--organism   Organism name (required)
```

#### `load_feature_dbxrefs`
```
--file       TSV: feature_accession<TAB>DB:accession (required)
--soterm     SO term of target features (required)
--organism   Organism name (required)
```

#### `load_similarity`
```
--file              XML file (BLAST or InterProScan) (required)
--format            blast-xml or interproscan-xml (required)
--program           Program name (required)
--programversion    Program version (required)
--so_query          SO term for query features (required)
--so_subject        SO term for subject features (required)
--org_query         Query organism name (required)
--org_subject       Subject organism name (required)
--algorithm         Algorithm name (optional)
--name              Analysis name (optional)
--description       Analysis description (optional)
```

#### `load_vcf`
```
--file       VCF file (bgzipped + tabix-indexed) (required)
--organism   Organism name (required)
--doi        Publication DOI (optional)
```

#### `load_orthomcl`
```
--file       OrthoMCL groups.txt file (required)
--organism   Organism name (required, unless --multispecies)
--multispecies  Multi-species mode (flag)
```

#### `load_rnaseq_info`
```
--file       TSV with sample metadata (required)
--organism   Organism name (required)
```

#### `load_rnaseq_data`
```
--file       TSV with expression values (required)
--organism   Organism name (required)
--soterm     SO term of features (required)
--norm       Normalization method name (optional)
```

#### `load_publication`
```
--file    BibTeX file (required)
```

#### `load_phylotree`
```
--file       Newick tree file (required)
--name       Tree name (required)
--organism   Organism name (required)
```

### Removal Commands

| Command | Key Arguments | Description |
|---|---|---|
| `remove_file` | `--name` (filename) | Removes all data loaded from the named file |
| `remove_analysis` | `--name` (analysis name) | Removes analysis and all associated features |
| `remove_feature_annotation` | `--soterm`, `--cvterm`, `--organism` | Removes specific annotation type |
| `remove_ontology` | `--name` (CV name) | Removes entire ontology |
| `remove_organism` | `--organism` (name) | Removes organism and all linked data |
| `remove_organisms` | (no args) | Removes ALL organisms |
| `remove_phylotree` | `--name` (tree name) | Removes phylogenetic tree |
| `remove_publication` | `--doi` (DOI string) | Removes publication by DOI |
| `remove_relationship` | `--type`, `--cv` | Removes feature relationships by type |

### Utility Commands

| Command | Description |
|---|---|
| `check_ids` | Validates that feature IDs in a file exist in the database |

---

## Data Loading Order (Critical)

The loading order is strictly enforced by foreign key dependencies:

```
1. Ontologies (RO → SO → GO)
2. Organisms
3. Publications (if DOIs will be referenced later)
4. Reference FASTA sequences
5. GFF3 features (requires reference sequences)
6. Feature annotations / dbxrefs
7. Similarity results (requires query + subject features)
8. Orthology / coexpression groups
9. RNA-seq metadata → RNA-seq data
10. VCF variants (requires reference sequences)
11. Elasticsearch index rebuild
```
