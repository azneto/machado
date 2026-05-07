# Loading InterProScan Results

In order to load an InterProScan results file, both the query and the subject records must be previously stored. The current version was tested for loading InterProScan analysis on **proteins**.

## Load InterProScan Subject Records

```bash
python manage.py load_similarity_matches --file interproscan_result.xml --format interproscan-xml
```

- Loading this file can be faster if you increase the number of threads (`--cpu`).

## Load InterProScan Similarity

```bash
python manage.py load_similarity --file interproscan_result.xml --format interproscan-xml \
    --so_query polypeptide --so_subject protein_match \
    --program interproscan --programversion 5 \
    --organism_query 'Oryza sativa' --organism_subject 'multispecies multispecies'
```

- Loading this file can be faster if you increase the number of threads (`--cpu`).

```bash
python manage.py load_similarity --help
```

| Parameter              | Description                                                                                      |
|------------------------|--------------------------------------------------------------------------------------------------|
| `--file` *             | InterProScan XML file                                                                            |
| `--format` *           | `interproscan-xml`                                                                               |
| `--so_query` *         | Query Sequence Ontology term (`polypeptide`)                                                     |
| `--so_subject` *       | Subject Sequence Ontology term (`protein_match`)                                                 |
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

If, for any reason, you need to remove an InterProScan result set, use the command `remove_analysis`.

```bash
python manage.py remove_analysis --help
```

- This command requires the analysis name (`Analysis.sourcename`).
