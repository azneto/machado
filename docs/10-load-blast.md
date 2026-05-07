# Loading BLAST Results

In order to load a BLAST XML result file, both the query and the subject records must be previously stored (see below). The current version was tested for loading BLAST analysis on **proteins**.

## Load BLAST Subject Records

In case you did a BLAST against a multispecies protein database, like NCBI's nr or Uniprot's trembl or swissprot, you need to load all subject matches before loading the result itself:

```bash
python manage.py load_similarity_matches --file blast_result.xml --format blast-xml
```

- Loading this file can be faster if you increase the number of threads (`--cpu`).

## Load BLAST

If all queries and subjects are already loaded you can run the following command to load a BLAST XML result:

```bash
python manage.py load_similarity --file blast_result.xml --format blast-xml \
    --so_query polypeptide --so_subject protein_match \
    --program diamond --programversion 0.9.24 \
    --organism_query 'Oryza sativa' --organism_subject 'multispecies multispecies'
```

- Loading this file can be faster if you increase the number of threads (`--cpu`).

```bash
python manage.py load_similarity --help
```

| Parameter              | Description                                                                                      |
|------------------------|--------------------------------------------------------------------------------------------------|
| `--file` *             | BLAST XML file                                                                                   |
| `--format` *           | `blast-xml`                                                                                      |
| `--so_query` *         | Query Sequence Ontology term (e.g. assembly, mRNA, polypeptide)                                  |
| `--so_subject` *       | Subject Sequence Ontology term (e.g. protein\_match)                                             |
| `--organism_query` *   | Query's organism name (e.g. *Oryza sativa*). Cannot be 'multispecies'.                           |
| `--organism_subject` * | Subject's organism name. Put `multispecies multispecies` if using a multispecies database.        |
| `--program` *          | Program                                                                                          |
| `--programversion` *   | Program version                                                                                  |
| `--name`               | Name                                                                                             |
| `--description`        | Description                                                                                      |
| `--algorithm`          | Algorithm                                                                                        |
| `--cpu`                | Number of threads                                                                                |

\* required fields

## Remove File

If, for any reason, you need to remove a BLAST result set, use the command `remove_analysis`.

```bash
python manage.py remove_analysis --help
```

- This command requires the analysis name (`Analysis.sourcename`).
