# Inserting a New Organism

## Insert Organism

Every data file you'll load (e.g. FASTA, GFF, BLAST) must belong to an organism. These are instructions to insert a new organism to the database **if you did NOT** load the NCBI taxonomy or if the organism you're working with is not included.

```bash
python manage.py insert_organism --genus 'Organismus' --species 'ineditus'
```

- There are optional fields you can provide. Please take a look at the command help (`--help`).

## Remove Organism

If, for any reason, you need to remove an organism, use the command `remove_organism`. Most data files you'll load depend on the organism record (e.g. FASTA, GFF, BLAST). **If you delete an organism, every data file you loaded that depends on it will be deleted on cascade.**

```bash
python manage.py remove_organism --help
```

- These commands require the following info: `Organism.genus` and `Organism.species`.
