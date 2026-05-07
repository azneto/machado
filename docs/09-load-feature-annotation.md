# Loading Feature Additional Info

Please notice the features must be loaded in advance. If the annotation or sequence was loaded previously, it will be replaced.

## Load Annotation

```bash
python manage.py load_feature_annotation --file feature_annotation.tab --soterm polypeptide --cvterm display --organism 'Arabidopsis thaliana'
```

- Loading this file can be faster if you increase the number of threads (`--cpu`).

```bash
python manage.py load_feature_annotation --help
```

| Parameter      | Description                                                                                                      |
|----------------|------------------------------------------------------------------------------------------------------------------|
| `--file` *     | Two-column tab separated file (`feature.accession<TAB>annotation text`)                                          |
| `--organism` * | Species name (e.g. *Homo sapiens*, *Mus musculus*)                                                               |
| `--soterm` *   | SO Sequence Ontology Term (e.g. mRNA, polypeptide)                                                               |
| `--cvterm` *   | cvterm.name from cv feature\_property (e.g. display, note, product, alias, ontology\_term, annotation)           |
| `--doi`        | DOI of a reference stored using `load_publication` (e.g. 10.1111/s12122-012-1313-4)                              |
| `--cpu`        | Number of threads                                                                                                |

\* required fields

### Remove Annotation

If, for any reason, you need to remove a feature annotation, use the command `remove_feature_annotation`.

```bash
python manage.py remove_feature_annotation --help
```

---

## Load Sequence

```bash
python manage.py load_feature_sequence --organism 'Arabidopsis thaliana' --file Athaliana_transcripts.fasta --soterm mRNA
```

- Loading this file can be faster if you increase the number of threads (`--cpu`).

```bash
python manage.py load_feature_sequence --help
```

| Parameter      | Description                                                          |
|----------------|----------------------------------------------------------------------|
| `--file` *     | FASTA file                                                           |
| `--organism` * | Species name (e.g. *Homo sapiens*, *Mus musculus*)                   |
| `--soterm` *   | SO Sequence Ontology Term (e.g. chromosome, assembly, mRNA, polypeptide) |
| `--cpu`        | Number of threads                                                    |

\* required fields

### Remove Sequence

If, for any reason, you need to remove a feature sequence, use the command `load_feature_sequence` itself and provide a FASTA file with no sequence. For example:

```text
>chr1

>chr2
```

---

## Load Publication

```bash
python manage.py load_feature_publication --organism 'Arabidopsis thaliana' --file feature_publication.tab
```

- Loading this file can be faster if you increase the number of threads (`--cpu`).

```bash
python manage.py load_feature_publication --help
```

| Parameter      | Description                                              |
|----------------|----------------------------------------------------------|
| `--file` *     | Two-column tab separated file (`feature.accession<TAB>DOI`) |
| `--organism` * | Species name (e.g. *Homo sapiens*, *Mus musculus*)       |
| `--cpu`        | Number of threads                                        |

\* required fields

### Remove Publication

If, for any reason, you need to remove a feature publication attribution, use the command `remove_publication`.

```bash
python manage.py remove_publication --help
```

---

## Load DBxRef

```bash
python manage.py load_feature_dbxrefs --organism 'Arabidopsis thaliana' --file feature_dbxrefs.tab --soterm mRNA
```

- Loading this file can be faster if you increase the number of threads (`--cpu`).

```bash
python manage.py load_feature_dbxrefs --help
```

| Parameter      | Description                                                             |
|----------------|-------------------------------------------------------------------------|
| `--file` *     | Two-column tab separated file (`feature.accession<TAB>db:dbxref`)       |
| `--organism` * | Species name (e.g. *Homo sapiens*, *Mus musculus*)                      |
| `--soterm` *   | SO Sequence Ontology Term (e.g. chromosome, assembly, mRNA, polypeptide) |
| `--cpu`        | Number of threads                                                       |

\* required fields
