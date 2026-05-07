# Loading OrthoMCL Results

## Load OrthoMCL

```bash
python manage.py load_orthomcl --file groups.txt
```

- Loading this file can be faster if you increase the number of threads (`--cpu`).

```bash
python manage.py load_orthomcl --help
```

| Parameter    | Description                              |
|--------------|------------------------------------------|
| `--file` *   | Output result from OrthoMCL software     |
| `--cpu`      | Number of threads                        |

\* required fields

## Remove Orthology

If, for any reason, you need to remove orthology relationships, use the command `remove_feature_annotation`.

```bash
python manage.py remove_feature_annotation --help
```

| Parameter              | Description                                        |
|------------------------|----------------------------------------------------|
| `--cvterm` *           | `orthologous group`                                |
| `--organism`           | Species name (e.g. *Homo sapiens*, *Mus musculus*) |

\* required fields
