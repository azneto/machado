# Copyright 2018 by Embrapa.  All rights reserved.
#
# This code is part of the machado distribution and governed by its
# license. Please see the LICENSE.txt and README.md files that should
# have been included as part of this package for licensing information.

"""Remove file."""

from machado.models import (
    Assay,
    Assayprop,
    Analysis,
    Analysisprop,
    Biomaterial,
    Biomaterialprop,
    Feature,
    Dbxrefprop,
    Project,
    Projectprop,
    AssayProject,
)
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand, CommandError
from machado.management.commands._base import HistoryCommandMixin


import os


class Command(HistoryCommandMixin, BaseCommand):
    """Remove file."""

    help = "Remove records and associated data linked to a specific file (CASCADE)"

    def add_arguments(self, parser):
        """Define the arguments."""
        parser.add_argument(
            "--name", help="Name of the file to be removed", required=True, type=str
        )

    def handle(self, name: str, verbosity: int = 0, **options):
        """Execute the main function."""
        filename = os.path.basename(name)
        # Handling Features
        if verbosity > 1:
            self.stdout.write(
                "Features: Deleting records linked to '{}' (CASCADE)...".format(
                    filename
                )
            )
        try:
            Feature.objects.filter(
                dbxref__Dbxrefprop_dbxref_Dbxref__value=filename
            ).delete()
            Dbxrefprop.objects.filter(value=filename).delete()
        except ObjectDoesNotExist:
            raise CommandError(
                "Features: Cannot remove '{}' (not found in database).".format(filename)
            )
        # Handling Projects
        if verbosity > 1:
            self.stdout.write(
                "Projects: Deleting records linked to '{}' (CASCADE)...".format(
                    filename
                )
            )
        try:
            project_ids = list(
                Projectprop.objects.filter(value=filename).values_list(
                    "project_id", flat=True
                )
            )
            AssayProject.objects.filter(project_id__in=project_ids).delete()
            Project.objects.filter(project_id__in=project_ids).delete()
            Projectprop.objects.filter(value=filename).delete()
        except ObjectDoesNotExist:
            raise CommandError(
                "Projects: Cannot remove '{}' (not found in database).".format(filename)
            )
        # Handling Assay
        if verbosity > 1:
            self.stdout.write(
                "Assays: Deleting records linked to '{}' (CASCADE)...".format(filename)
            )
        try:
            assay_ids = list(
                Assayprop.objects.filter(value=filename).values_list(
                    "assay_id", flat=True
                )
            )
            AssayProject.objects.filter(assay_id__in=assay_ids).delete()
            Assay.objects.filter(assay_id__in=assay_ids).delete()
        except ObjectDoesNotExist:
            raise CommandError(
                "Assays: Cannot remove '{}' (not found in database).".format(filename)
            )
        # Handling Biomaterial
        if verbosity > 1:
            self.stdout.write(
                "Biomaterials: Deleting records linked to '{}' (CASCADE)...".format(
                    filename
                )
            )
        try:
            biomaterial_ids = list(
                Biomaterialprop.objects.filter(value=filename).values_list(
                    "biomaterial_id", flat=True
                )
            )
            Biomaterial.objects.filter(biomaterial_id__in=biomaterial_ids).delete()
            Biomaterialprop.objects.filter(value=filename).delete()
        except ObjectDoesNotExist:
            raise CommandError(
                "Biomaterials: Cannot remove '{}' (not found in database).".format(
                    filename
                )
            )
        # Handling Analysis
        if verbosity > 1:
            self.stdout.write(
                "Analysis: Deleting records linked to '{}' (CASCADE)...".format(
                    filename
                )
            )
        try:
            analysis_ids = list(
                Analysisprop.objects.filter(value=filename).values_list(
                    "analysis_id", flat=True
                )
            )
            Analysis.objects.filter(analysis_id__in=analysis_ids).delete()
        except ObjectDoesNotExist:
            raise CommandError(
                "Analysis: Cannot remove '{}' (not found in database).".format(filename)
            )

        if verbosity > 0:
            self.stdout.write(self.style.SUCCESS("Operation completed successfully."))
