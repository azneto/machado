# 2. Data Loading

The Chado schema heavily relies on **Ontologies** to integrate different datasets. Therefore ontologies must be the first data loaded.

Inside the `extras` directory, there's a file named `sample.tar.gz` that might be helpful. It contains a few small FASTA and GFF files, together with a README file with examples of command lines.

## Loading order

The recommended loading order is:

1. [Ontologies](03-load-ontologies.md) — **required**, must be loaded first
2. [Taxonomy](04-load-taxonomy.md) — optional, but useful for multi-organism instances
3. [Organism](05-insert-organism.md) — required if taxonomy was not loaded
4. [Publication](06-load-publication.md) — optional, allows linking DOIs to data
5. [FASTA](07-load-fasta.md) — reference genome sequences
6. [GFF](08-load-gff.md) — gene models / genome annotations
7. [Feature Additional Info](09-load-feature-annotation.md) — annotations, sequences, publications, cross-references
8. [BLAST](10-load-blast.md) — similarity search results
9. [InterProScan](11-load-interproscan.md) — protein domain analysis
10. [OrthoMCL](12-load-orthomcl.md) — orthology groups
11. [RNA-seq](13-load-rnaseq.md) — expression data
12. [Coexpression](14-load-coexpression.md) — coexpression pairs and clusters
13. [VCF](15-load-vcf.md) — variant data

> **Tip:** Most `load_*` commands accept `--cpu` to increase the number of threads and speed up loading.
