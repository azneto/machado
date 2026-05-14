# Copyright 2018 by Embrapa.  All rights reserved.
#
# This code is part of the machado distribution and governed by its
# license. Please see the LICENSE.txt and README.md files that should
# have been included as part of this package for licensing information.

"""Remove relationship."""

from machado.models import Cvterm, FeatureRelationship
import os

from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand, CommandError
from machado.management.commands._base import HistoryCommandMixin
from django.db.utils import IntegrityError

from machado.loaders.exceptions import ImportingError


class Command(HistoryCommandMixin, BaseCommand):
    """Remove relationship."""

    help = "Remove feature relationships associated with a specific file"

    def add_arguments(self, parser):
        """Define the arguments."""
        parser.add_argument(
            "--file",
            help="Path to the file whose relationships should be removed",
            required=True,
            type=str,
        )

    def handle(self, file: str, verbosity: int = 0, **options):
        """Execute the main function."""
        # get cvterm for located in
        try:
            cvterm = Cvterm.objects.get(name="located in", cv__name="relationship")
        except IntegrityError as e:
            raise ImportingError(e)
        filename = os.path.basename(file)
        if verbosity > 0:
            self.stdout.write("Removing relationships...")
        try:
            FeatureRelationship.objects.filter(
                FeatureRelationshipprop_feature_relationship_FeatureRelationship__value=filename,
                FeatureRelationshipprop_feature_relationship_FeatureRelationship__type=cvterm,
            ).delete()

            if verbosity > 0:
                self.stdout.write(
                    self.style.SUCCESS("Operation completed successfully.")
                )
        except IntegrityError as e:
            raise CommandError(
                "Unable to delete records. Please ensure that any relationships "
                "dependent on '{}' are removed first. Error: {}".format(filename, e)
            )
        except ObjectDoesNotExist:
            raise CommandError(
                "Cannot remove '{}' (not found in database).".format(filename)
            )
