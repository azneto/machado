# Copyright 2018 by Embrapa.  All rights reserved.
#
# This code is part of the machado distribution and governed by its
# license. Please see the LICENSE.txt and README.md files that should
# have been included as part of this package for licensing information.

"""Remove phylotree."""

from machado.models import Phylotree, Phylonode, PhylonodeOrganism
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand, CommandError
from machado.management.commands._base import HistoryCommandMixin


class Command(HistoryCommandMixin, BaseCommand):
    """Remove phylotree."""

    help = "Remove a phylotree and its associated nodes from the database"

    def add_arguments(self, parser):
        """Define the arguments."""
        parser.add_argument(
            "--name", help="Name of the phylotree to remove", required=True, type=str
        )

    def handle(self, name: str, verbosity: int = 1, **options):
        """Execute the main function."""
        try:
            if verbosity > 0:
                self.stdout.write(
                    "Deleting phylotree '{}' and all associated records...".format(name)
                )
            phylotree = Phylotree.objects.get(name=name)
            phylonode_ids = list(
                Phylonode.objects.filter(phylotree=phylotree).values_list(
                    "phylonode_id", flat=True
                )
            )
            PhylonodeOrganism.objects.filter(phylonode_id__in=phylonode_ids).delete()
            Phylonode.objects.filter(phylotree=phylotree).delete()
            phylotree.delete()

            if verbosity > 0:
                self.stdout.write(
                    self.style.SUCCESS("Operation completed successfully.")
                )
        except ObjectDoesNotExist:
            raise CommandError(
                "Cannot remove '{}' (not found in database).".format(name)
            )
