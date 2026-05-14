# Copyright 2018 by Embrapa.  All rights reserved.
#
# This code is part of the machado distribution and governed by its
# license. Please see the LICENSE.txt and README.md files that should
# have been included as part of this package for licensing information.

"""Remove analysis."""

from machado.models import (
    Acquisition,
    Analysisprop,
    Analysis,
    Analysisfeature,
    Quantification,
    Cvterm,
    Feature,
    Featureloc,
    FeatureCvterm,
    FeatureCvtermprop,
    FeatureRelationship,
    FeatureRelationshipprop,
)
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand, CommandError
from machado.management.commands._base import HistoryCommandMixin
from tqdm import tqdm


class Command(HistoryCommandMixin, BaseCommand):
    """Remove analysis."""

    help = "Remove analysis records and associated child data (CASCADE)"

    def add_arguments(self, parser):
        """Define the arguments."""
        parser.add_argument(
            "--name",
            help="Name of the analysis file to remove (e.g., source filename)",
            required=True,
            type=str,
        )

    def handle(self, name: str, verbosity: int = 1, **options):
        """Execute the main function."""
        if verbosity > 0:
            self.stdout.write(
                "Deleting analysis '{}' and all associated records...".format(name)
            )

        cvterm_contained_in = Cvterm.objects.get(
            name="located in", cv__name="relationship"
        )
        analysisprop_list = Analysisprop.objects.filter(
            value=name, type_id=cvterm_contained_in.cvterm_id
        )

        if analysisprop_list.count() > 0:
            for analysisprop in tqdm(
                analysisprop_list,
                total=len(analysisprop_list),
                disable=False if verbosity > 0 else True,
            ):
                analysis = Analysis.objects.get(analysis_id=analysisprop.analysis_id)
                # remove quantification and aquisition if exists...
                try:
                    quantification = Quantification.objects.get(analysis=analysis)
                    Acquisition.objects.filter(
                        acquisition_id=quantification.acquisition_id
                    ).delete()
                    quantification.delete()
                except ObjectDoesNotExist:
                    pass
                # remove analysisfeatures and others if exists...
                try:
                    cr_ids = list(
                        FeatureCvtermprop.objects.filter(
                            type=cvterm_contained_in, value=analysis.sourcename
                        ).values_list("feature_cvterm_id", flat=True)
                    )
                    FeatureCvterm.objects.filter(feature_cvterm_id__in=cr_ids).delete()

                    fr_ids = list(
                        FeatureRelationshipprop.objects.filter(
                            type=cvterm_contained_in, value=analysis.sourcename
                        ).values_list("feature_relationship_id", flat=True)
                    )
                    FeatureRelationship.objects.filter(
                        feature_relationship_id__in=fr_ids
                    ).delete()

                    feature_ids = list(
                        Analysisfeature.objects.filter(analysis=analysis).values_list(
                            "feature_id", flat=True
                        )
                    )
                    Featureloc.objects.filter(feature_id__in=feature_ids).delete()
                    # remove only features created by load_similarity
                    # type == match_part
                    Feature.objects.filter(
                        feature_id__in=feature_ids, type__name="match_part"
                    ).delete()
                    Analysisfeature.objects.filter(analysis=analysis).delete()
                except ObjectDoesNotExist:
                    pass
                # finally removes analysis...
                analysis.delete()
            if verbosity > 0:
                self.stdout.write(
                    self.style.SUCCESS("Operation completed successfully.")
                )
        else:
            raise CommandError(
                "Cannot remove '{}' (not found in database).".format(name)
            )
