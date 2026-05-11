# Copyright 2018 by Embrapa.  All rights reserved.
#
# This code is part of the machado distribution and governed by its
# license. Please see the LICENSE.txt and README.md files that should
# have been included as part of this package for licensing information.
"""Search forms — PostgreSQL full-text search."""

from django import forms
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import Q

from machado.models import FeatureSearchIndex

# Facets that are stored as JSON arrays (need __contains lookups)
_ARRAY_FACETS = {
    "analyses",
    "biomaterial",
    "treatment",
    "doi",
    "orthologs_coexpression",
}

# The "analyses" facet uses AND logic; all others use OR.
_AND_FACETS = {"analyses"}


class FeatureSearchForm(forms.Form):
    """Search form backed by PostgreSQL full-text search."""

    q = forms.CharField(required=False)

    def search(self, selected_facets=None):
        """Return a filtered queryset of FeatureSearchIndex rows."""
        qs = FeatureSearchIndex.objects.select_related("feature").all()
        q = self.cleaned_data.get("q", "").strip()

        # ── Apply facet filters ──────────────────────────────────────────
        if selected_facets:
            qs = self._apply_facets(qs, selected_facets)

        # ── Apply full-text query ────────────────────────────────────────
        if q:
            query = SearchQuery(q, config="english", search_type="websearch")
            qs = qs.filter(search_vector=query).annotate(
                rank=SearchRank("search_vector", query)
            )

        return qs

    @staticmethod
    def _apply_facets(qs, selected_facets):
        """Apply facet filters with AND for 'analyses', OR for others."""
        grouped = {}
        for facet_str in selected_facets:
            field, value = facet_str.split(":", 1)
            grouped.setdefault(field, []).append(value)

        for field, values in grouped.items():
            if field in _AND_FACETS:
                # AND logic: every selected value must be present
                for v in values:
                    qs = qs.filter(**{f"{field}__contains": [v]})
            elif field in _ARRAY_FACETS:
                # OR logic for array fields
                q_obj = Q()
                for v in values:
                    q_obj |= Q(**{f"{field}__contains": [v]})
                qs = qs.filter(q_obj)
            else:
                # Scalar fields — OR via __in
                qs = qs.filter(**{f"{field}__in": values})

        return qs
