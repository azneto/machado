# Copyright 2018 by Embrapa.  All rights reserved.
#
# This code is part of the machado distribution and governed by its
# license. Please see the LICENSE.txt and README.md files that should
# have been included as part of this package for licensing information.

"""Load relations ontology."""

import obonet
from django.core.management.base import BaseCommand
from machado.management.commands._base import HistoryCommandMixin
from tqdm import tqdm

from machado.loaders.common import FileValidator
from machado.loaders.ontology import OntologyLoader


class Command(HistoryCommandMixin, BaseCommand):
    """Load relations ontology."""

    help = "Load Relations Ontology (RO) from an OBO file"

    def add_arguments(self, parser):
        """Define the arguments."""
        parser.add_argument(
            "--file",
            help="Path to the Relations Ontology (RO) OBO file",
            required=True,
            type=str,
        )

    def handle(self, file: str, verbosity: int = 1, **options):
        """Execute the main function."""
        FileValidator().validate(file)
        # Load the ontology file
        with open(file) as obo_file:
            G = obonet.read_obo(obo_file)

        if verbosity > 0:
            self.stdout.write("Preprocessing data...")

        cv_name = "relationship"

        # Initializing ontology
        ontology = OntologyLoader(cv_name)
        # Load typedefs as Dbxrefs and Cvterm
        if verbosity > 0:
            self.stdout.write("Loading definitions...")

        for data in tqdm(G.graph["typedefs"], disable=False if verbosity > 0 else True):
            ontology.store_type_def(data)

        if verbosity > 0:
            self.stdout.write(self.style.SUCCESS("Operation completed successfully."))
