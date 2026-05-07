# Loading Publication Files

## Load Publication

```bash
python manage.py load_publication --file reference.bib
```

- Loading this file can be faster if you increase the number of threads (`--cpu`).

## Remove Publication

If, for any reason, you need to remove a publication, use the command `remove_publication`. **If you delete a publication, every record that depends on it will be deleted on cascade, with the exception of the Dbxref field that contains the DOI accession.**

```bash
python manage.py remove_publication --help
```
