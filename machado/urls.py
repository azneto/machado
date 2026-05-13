# Copyright 2018 by Embrapa.  All rights reserved.
#
# This code is part of the machado distribution and governed by its
# license. Please see the LICENSE.txt and README.md files that should
# have been included as part of this package for licensing information.

"""URLs."""

from django.conf import settings
from django.urls import re_path
from django.views.decorators.cache import cache_page

from machado.views import common

try:
    CACHE_TIMEOUT = settings.CACHE_TIMEOUT
except AttributeError:
    CACHE_TIMEOUT = 60 * 60

from machado.views import feature, search, autocomplete, jbrowse

urlpatterns = [
    re_path(
        r"autocomplete/",
        autocomplete.AutocompleteView.as_view(),
        name="autocomplete_html",
    ),
    re_path(
        r"^api/jbrowse/stats/global$", jbrowse.jbrowse_global, name="jbrowse_global"
    ),
    re_path(r"^api/jbrowse/names$", jbrowse.jbrowse_names, name="jbrowse_names"),
    re_path(
        r"^api/jbrowse/refSeqs.json$", jbrowse.jbrowse_refseqs, name="jbrowse_refseqs"
    ),
    re_path(
        r"^api/jbrowse/features/(?P<refseq>.+)$",
        jbrowse.jbrowse_features,
        name="jbrowse_features",
    ),
    re_path(
        r"feature/",
        cache_page(CACHE_TIMEOUT)(feature.FeatureView.as_view()),
        name="feature",
    ),
    re_path(
        r"data/",
        cache_page(CACHE_TIMEOUT)(common.DataSummaryView.as_view()),
        name="data_numbers",
    ),
    re_path(
        r"find/",
        cache_page(CACHE_TIMEOUT)(search.FeatureSearchView.as_view()),
        name="feature_search",
    ),
    re_path(
        r"export/",
        cache_page(CACHE_TIMEOUT)(search.FeatureSearchExportView.as_view()),
        name="feature_search_export",
    ),
    re_path(r"^$", cache_page(CACHE_TIMEOUT)(common.HomeView.as_view()), name="home"),
]
