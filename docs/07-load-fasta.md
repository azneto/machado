# Loading FASTA Files

This command is mostly used to load the reference genome. The reference sequences are exclusively used to feed JBrowse.

If the reference sequences are really long (>200 Mbp), there may be memory issues during the loading process and JBrowse may take too long to render the tracks. To avoid that, it's possible to use the parameter `--nosequence` and configure JBrowse to get the reference data from a FASTA file.

## Load FASTA

```bash
python manage.py load_fasta --file organism_chrs.fa --soterm chromosome --organism 'Arabidopsis thaliana'
```

- Loading this file can be faster if you increase the number of threads (`--cpu`).

```bash
python manage.py load_fasta --help
```

| Parameter       | Description                                                                         |
|-----------------|-------------------------------------------------------------------------------------|
| `--file` *      | FASTA file                                                                          |
| `--organism` *  | Species name (e.g. *Homo sapiens*, *Mus musculus*)                                  |
| `--soterm` *    | SO Sequence Ontology Term (e.g. chromosome, assembly)                               |
| `--description` | Description                                                                         |
| `--url`         | URL                                                                                 |
| `--doi`         | DOI of a reference stored using `load_publication` (e.g. 10.1111/s12122-012-1313-4) |
| `--nosequence`  | Don't load the sequences                                                            |
| `--cpu`         | Number of threads                                                                   |

\* required fields

## Remove File

If, for any reason, you need to remove a FASTA file, use the command `remove_organism`. Most data files you'll load depend on the organism record (e.g. FASTA, GFF, BLAST). **If you delete an organism, every data file you loaded that depends on it will be deleted on cascade.**

```bash
python manage.py remove_organism --help
```

- These commands require the following info: `Organism.genus` and `Organism.species`.
