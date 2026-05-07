# Loading Ontologies

The ontologies are required and must be loaded first.

## Relations Ontology

RO is an ontology of relations for use with biological ontologies.

- **URL:** <https://github.com/oborel/obo-relations>
- **File:** `ro.obo`

```bash
python manage.py load_relations_ontology --file ro.obo
```

## Sequence Ontology

Collection of SO Ontologies.

- **URL:** <https://github.com/The-Sequence-Ontology/SO-Ontologies>
- **File:** `so.obo`

```bash
python manage.py load_sequence_ontology --file so.obo
```

## Gene Ontology

Source ontology files for the Gene Ontology.

- **URL:** <http://current.geneontology.org/ontology/>
- **File:** `go.obo`

```bash
python manage.py load_gene_ontology --file go.obo
```

- Loading the Gene Ontology can be faster if you increase the number of threads (`--cpu`).
- After loading, the following records will be created in the Cv table: `gene_ontology`, `external`, `molecular_function`, `cellular_component`, and `biological_process`.

## Remove Ontology

If, for any reason, you need to remove an ontology, use the command `remove_ontology`. Most data files you'll load depend on the ontologies (e.g. FASTA, GFF, BLAST). You should **never** delete an ontology after having data files loaded.

```bash
python manage.py remove_ontology --help
```

- This command requires the name of the ontology (`Cv.name`).
- There are dependencies between the Gene Ontology records, therefore you need to delete the entry `external` first.
