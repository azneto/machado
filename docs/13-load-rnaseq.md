# Loading RNA-seq Data

## Load RNA-seq Information

Before inserting RNA-seq count tables, it is needed to input information about the experiments and samples from which the data was generated. In machado we focus on the GEO/NCBI database as a source for RNA-seq experiments information and data.

From the GEO/NCBI database you get identifiers for different *series* (e.g. GSE85653) that describe the studies/projects as a whole. From the GEO series you get identifiers for biosamples (or, in Chado lingo, biomaterials — e.g. GSM2280286). From the GEO biosamples you get identifiers for RNA-seq experiments (or assays), usually from the SRA database (e.g. SRR4033018). SRA identifiers link to the raw data you can analyse.

In machado, it is necessary to input a `.csv` file with information for all SRA data files regarding RNA-seq assays that will be loaded.

This file must have the following fields in each line:

```
"Organism", "GEO series", "GEO sample", "SRA identifier", "Assay description", "Treatment description", "Biomaterial description", "Date"
```

A sample line:

```csv
Oryza sativa,GSE85653,GSM2280286,SRR4033018,Heat leaf rep1,Heat stress,Leaf,May-30-2018
```

To load such a file:

```bash
python manage.py load_rnaseq_info --file file.csv --biomaterialdb GEO --assaydb SRA
```

- Loading this file can be faster if you increase the number of threads (`--cpu`).

```bash
python manage.py load_rnaseq_info --help
```

| Parameter          | Description                                  |
|--------------------|----------------------------------------------|
| `--file` *         | `.csv` file                                  |
| `--biomaterialdb`  | Biomaterial database info (e.g. `GEO`)       |
| `--assaydb`        | Assay database info (e.g. `SRA`)             |
| `--cpu`            | Number of threads                            |

\* required field

### Remove RNA-seq Information

If, for any reason, you need to remove RNA-seq information, use the command `remove_file --name`. **Every relation from the filename (e.g. `file.csv`) will be deleted on cascade.**

```bash
python manage.py remove_file --help
```

- This command requires the file name used as input to load RNA-seq information.

---

## Load RNA-seq Data

To load expression count tables for RNA-seq data, a tabular file should be loaded. This file can contain data from several RNA-seq experiments (assays) per column. The file should have the following header:

```
Gene identifier    SRA Identifier 1    SRA Identifier 2    ...    SRA Identifier n
```

Example header for a file with two assays/experiments:

```
gene    SRR5167848.htseq    SRR2302912.htseq
```

The body of the table is composed of the gene identifier followed by the counts for each gene, in each experiment:

```
AT2G44195.1.TAIR10     0.0     0.6936967934559419
```

Note that the count fields can have floats or integers, depending on the normalization used (usually TPM, FPKM or raw counts).

The gene identifier is supposed to already be loaded as a feature, usually from the organism's genome annotation GFF file. We used the output of the LSTrAP program as standard format for this file.

```bash
python manage.py load_rnaseq_data --file file.tab --organism 'Oryza sativa' --programversion 1.3 --assaydb SRA
```

- As default the program name is `LSTrAP` but can be changed with `--program`.
- The data is by default taken as normalized (TPM, FPKM, etc.) but can be changed with `--norm`.
- Loading this file can be faster if you increase the number of threads (`--cpu`).

```bash
python manage.py load_rnaseq_data --help
```

| Parameter          | Description                                                                                |
|--------------------|--------------------------------------------------------------------------------------------|
| `--file`           | Tabular text file with gene counts per line                                                |
| `--organism`       | Scientific name (e.g. *Oryza sativa*)                                                      |
| `--programversion` | Version of the software (e.g. `1.3`)                                                       |
| `--name`           | Optional name                                                                              |
| `--description`    | Optional description                                                                       |
| `--algorithm`      | Optional algorithm description                                                             |
| `--assaydb`        | Optional assay database info (e.g. `SRA`)                                                  |
| `--timeexecuted`   | Optional date software was run. Mandatory format: e.g. `Oct-16-2016`                       |
| `--program`        | Optional name of the software (default: `LSTrAP`)                                         |
| `--norm`           | Optional. Normalized data: `1` = yes (TPM, FPKM, etc.); `0` = no (raw counts); default `1` |

### Remove RNA-seq Data

If, for any reason, you need to remove RNA-seq data, use the command `remove_file --name`. **Every relation from the filename (e.g. `file.tab`) will be deleted on cascade.**

```bash
python manage.py remove_file --help
```

- This command requires the file name used as input to load RNA-seq data.
