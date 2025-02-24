# Copyright 2018 by Embrapa.  All rights reserved.
#
# This code is part of the machado distribution and governed by its
# license. Please see the LICENSE.txt and README.md files that should
# have been included as part of this package for licensing information.

"""Remove organism."""
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand, CommandError
from machado.loaders.common import retrieve_organism
from machado.models import History


class Command(BaseCommand):
    """Remove organism."""

    help = "Remove organism"

    def add_arguments(self, parser):
        """Define the arguments."""
        parser.add_argument(
            "--organism",
            help="Species name (eg. Homo sapiens, Mus musculus)",
            required=True,
            type=str,
        )

    def handle(self, organism: str, verbosity: int = 1, **options):
        """Execute the main function."""
        history_obj = History()
        history_obj.start(command="remove_organism", params=locals())
        try:
            organism_obj = retrieve_organism(organism)
            if organism_obj:
                organism_obj.delete()
                history_obj.success(description="{} removed".format(organism))
                if verbosity > 0:
                    self.stdout.write(self.style.SUCCESS("{} removed".format(organism)))

        except ObjectDoesNotExist as e:
            history_obj.failure(description=str(e))
            raise CommandError("Organism does not exist in database!")
