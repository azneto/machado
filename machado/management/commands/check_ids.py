# Copyright 2018 by Embrapa.  All rights reserved.
#
# This code is part of the machado distribution and governed by its
# license. Please see the LICENSE.txt and README.md files that should
# have been included as part of this package for licensing information.

"""Check IDs."""

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from machado.loaders.common import retrieve_feature_id, FileValidator, retrieve_organism
from django.core.management.base import BaseCommand
from machado.management.commands._base import HistoryCommandMixin


class Command(HistoryCommandMixin, BaseCommand):
    """Check IDs."""

    help = "Verify the existence of feature IDs in the database"

    def add_arguments(self, parser):
        """Define the arguments."""
        parser.add_argument(
            "--file",
            help="Path to the file containing a list of IDs in the first column",
            required=True,
            type=str,
        )
        parser.add_argument(
            "--organism",
            help="Scientific name of the species (e.g., Homo sapiens)",
            required=True,
            type=str,
        )
        parser.add_argument(
            "--soterms",
            help="Sequence Ontology (SO) terms to check (e.g., gene, mRNA, miRNA)",
            required=True,
            nargs="+",
            type=str,
        )

    def handle(
        self, file: str, organism: str, soterms: list, verbosity: int = 1, **options
    ) -> None:
        """Execute the main function."""
        if verbosity > 0:
            self.stdout.write("Loading data...")

        FileValidator().validate(file)
        organism = retrieve_organism(organism)
        f = open(file, "r+")
        for line in f.readlines():
            notfound = set()
            accession = line.split()[0]
            for soterm in soterms:
                try:
                    retrieve_feature_id(
                        accession=accession, soterm=soterm, organism=organism
                    )
                    break
                except ObjectDoesNotExist:
                    notfound.add(soterm)
                except MultipleObjectsReturned:
                    self.stdout.write(
                        "Warning: '{}' matches multiple records.\n".format(accession)
                    )
                    break
            if len(notfound) == len(soterms):
                self.stdout.write(
                    "ID '{}' not found for specified terms {}.\n".format(
                        accession, sorted(list(notfound))
                    )
                )
        f.close()

        if verbosity > 0:
            self.stdout.write(self.style.SUCCESS("ID verification completed."))
