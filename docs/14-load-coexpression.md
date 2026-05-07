# Loading Coexpression Analyses

## Load Coexpression Correlated Pairs

Coexpression analyses usually generate correlation statistics regarding gene sets in a pairwise manner. For example, LSTrAP can generate a table with the Pearson correlation coefficient for every pair of genes in an RNA-seq experiment.

To load such a table into machado, the file must be headless and tab separated, with the two first columns containing the correlated pair of IDs for the genes/features and the third column containing the correlation coefficient. In the case of the LSTrAP software output, the coefficient is subtracted by 0.7 for normalization.

A sample from such a table:

```
AT2G44195.1.TAIR10      AT1G30080.1.TAIR10      0.18189286870895194
AT2G44195.1.TAIR10      AT5G24750.1.TAIR10      0.1715779378273995
```

> **Note:** The feature pairs from columns 1 and 2 need to be loaded previously.

To load such a table:

```bash
python manage.py load_coexpression_pairs --organism 'Arabidopsis thaliana' --file pcc.mcl.txt
```

- Loading this file can be faster if you increase the number of threads (`--cpu`).

```bash
python manage.py load_coexpression_pairs --help
```

| Parameter      | Description                                            |
|----------------|--------------------------------------------------------|
| `--file` *     | Coexpression pairs file (e.g. `pcc.mcl.txt`)           |
| `--organism` * | Species name (e.g. *Homo sapiens*, *Mus musculus*)     |
| `--soterm`     | Sequence ontology term (default: `mRNA`)               |
| `--cpu`        | Number of threads                                      |

\* example output file from LSTrAP software

### Remove Coexpression Pairs

If, for any reason, you need to remove coexpression pair analyses, pass the filename used to load the analyses to the `remove_relationship` command. **Every coexpression relation from the file will be deleted on cascade.**

```bash
python manage.py remove_relationship --help
```

| Parameter    | Description                                        |
|--------------|----------------------------------------------------|
| `--file` *   | Coexpression file (e.g. `mcl.clusters.txt`)        |

---

## Load Coexpression Clusters

Another type of coexpression analysis involves clustering features using their correlation values. LSTrAP does this using the `mcl` software. The input file must be headless and tab separated, with each line representing one cluster and each column representing one gene/feature from that cluster. The first column should represent the cluster name in the format `<cluster_name>:`.

Three-cluster sample (the third line is an orphaned cluster with only one individual — orphaned clusters are discarded):

```
ath_1:    AT3G18715.1.TAIR10      AT3G08790.1.TAIR10      AT5G42230.1.TAIR10
ath_2:    AT1G27040.1.TAIR10      AT1G71692.1.TAIR10
ath_3:    AT5G24750.1.TAIR10
```

> **Note:** The genes/features from each column must be loaded previously.

To load such a file:

```bash
python manage.py load_coexpression_clusters --file mcl.clusters.txt --organism 'Arabidopsis thaliana'
```

- Loading this file can be faster if you increase the number of threads (`--cpu`).

```bash
python manage.py load_coexpression_clusters --help
```

| Parameter      | Description                                            |
|----------------|--------------------------------------------------------|
| `--file` *     | Clusters file (e.g. `mcl.clusters.txt`)                |
| `--organism`   | Scientific name (e.g. *Arabidopsis thaliana*)          |
| `--soterm`     | Sequence ontology term (default: `mRNA`)               |
| `--cpu`        | Number of threads                                      |

### Remove Coexpression Clusters

If, for any reason, you need to remove coexpression cluster analyses, pass the controlled vocabulary term `coexpression group` and the organism scientific name to the command `remove_feature_annotation`. **Every coexpression group relation from that organism will be deleted on cascade.**

```bash
python manage.py remove_feature_annotation --help
```

| Parameter    | Description                                        |
|--------------|----------------------------------------------------|
| `--cvterm` * | `coexpression group`                               |
| `--organism` | Scientific name (e.g. *Oryza sativa*)              |
