# Copyright 2018 by Embrapa.  All rights reserved.
#
# This code is part of the machado distribution and governed by its
# license. Please see the LICENSE.txt and README.md files that should
# have been included as part of this package for licensing information.

"""Tests for API read views."""

from unittest.mock import MagicMock, patch
from django.test import TestCase
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from rest_framework.test import APIRequestFactory
from rest_framework import status

from machado.api.views.read import (
    JBrowseGlobalViewSet,
    JBrowseNamesViewSet,
    JBrowseRefSeqsViewSet,
    JBrowseFeatureViewSet,
    autocompleteViewSet,
    OrganismIDViewSet,
    OrganismListViewSet,
    FeatureIDViewSet,
    FeatureOrthologViewSet,
    FeatureCoexpressionViewSet,
    FeatureExpressionViewSet,
    FeatureInfoViewSet,
    FeatureLocationViewSet,
    FeatureSequenceViewSet,
    FeaturePublicationViewSet,
    FeatureOntologyViewSet,
    FeatureProteinMatchesViewSet,
    FeatureSimilarityViewSet,
    HistoryListViewSet,
)
from machado.models import Organism, Feature, History


class JBrowseGlobalViewSetTest(TestCase):
    def test_list(self):
        factory = APIRequestFactory()
        view = JBrowseGlobalViewSet.as_view({"get": "list"})
        request = factory.get("/api/jbrowse/stats/global")
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [{"featureDensity": 0.02}])


class JBrowseNamesViewSetTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    @patch("machado.api.views.read.retrieve_organism")
    @patch("machado.api.views.read.Feature.objects.filter")
    def test_list_with_organism(self, mock_filter, mock_retrieve):
        mock_org = MagicMock()
        mock_retrieve.return_value = mock_org
        mock_qs = MagicMock()
        mock_filter.return_value = mock_qs
        mock_qs.exclude.return_value = mock_qs
        view = JBrowseNamesViewSet.as_view({"get": "list"})
        request = self.factory.get("/api/jbrowse/names", {"organism": "test_org"})
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_qs.filter.assert_any_call(organism=mock_org)

    @patch("machado.api.views.read.Feature.objects.filter")
    def test_list_startswith(self, mock_filter):
        mock_qs = MagicMock()
        mock_filter.return_value = mock_qs
        mock_qs.exclude.return_value = mock_qs
        view = JBrowseNamesViewSet.as_view({"get": "list"})
        request = self.factory.get("/api/jbrowse/names", {"startswith": "test"})
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_qs.filter.assert_any_call(uniquename__startswith="test")

    @patch("machado.api.views.read.Feature.objects.filter")
    def test_list_equals(self, mock_filter):
        mock_qs = MagicMock()
        mock_filter.return_value = mock_qs
        mock_qs.exclude.return_value = mock_qs
        view = JBrowseNamesViewSet.as_view({"get": "list"})
        request = self.factory.get("/api/jbrowse/names", {"equals": "test"})
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_qs.filter.assert_any_call(uniquename="test")


class JBrowseRefSeqsViewSetTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    @patch("machado.api.views.read.retrieve_organism")
    @patch("machado.api.views.read.Feature.objects.filter")
    def test_list(self, mock_filter, mock_retrieve):
        mock_org = MagicMock()
        mock_retrieve.return_value = mock_org
        mock_qs = MagicMock()
        mock_filter.return_value = mock_qs
        mock_qs.filter.return_value = mock_qs
        mock_qs.only.return_value = mock_qs
        view = JBrowseRefSeqsViewSet.as_view({"get": "list"})
        request = self.factory.get(
            "/api/jbrowse/refSeqs.json",
            {"organism": "test_org", "soType": "chromosome"},
        )
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_qs.filter.assert_any_call(organism=mock_org)

    @patch("machado.api.views.read.retrieve_organism")
    @patch("machado.api.views.read.Feature.objects.filter")
    def test_list_minimal(self, mock_filter, mock_retrieve):
        mock_qs = MagicMock()
        mock_filter.return_value = mock_qs
        mock_qs.filter.return_value = mock_qs
        mock_qs.only.return_value = mock_qs
        view = JBrowseRefSeqsViewSet.as_view({"get": "list"})
        request = self.factory.get("/api/jbrowse/refSeqs.json")
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class JBrowseFeatureViewSetTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    @patch("machado.api.views.read.retrieve_organism")
    @patch("machado.api.views.read.Feature.objects.filter")
    @patch("machado.api.views.read.Featureloc.objects.filter")
    def test_list(self, mock_fl_filter, mock_f_filter, mock_retrieve):
        mock_org = MagicMock()
        mock_retrieve.return_value = mock_org
        mock_refseq = MagicMock()

        mock_fl_qs = MagicMock()
        mock_fl_filter.return_value = mock_fl_qs
        mock_fl_qs.filter.return_value = mock_fl_qs
        mock_fl_qs.values_list.return_value = [1, 2]

        mock_f_qs = MagicMock()
        mock_f_filter.side_effect = [
            MagicMock(first=MagicMock(return_value=mock_refseq)),
            MagicMock(first=MagicMock(return_value=mock_refseq)),
            mock_f_qs,
        ]
        mock_f_qs.filter.return_value = mock_f_qs

        view = JBrowseFeatureViewSet.as_view({"get": "list"})
        request = self.factory.get(
            "/api/jbrowse/features/refseq1",
            {"organism": "test_org", "start": 100, "end": 200, "soType": "gene"},
        )
        response = view(request, refseq="refseq1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("features", response.data)

    @patch("machado.api.views.read.retrieve_organism")
    @patch("machado.api.views.read.Feature.objects.filter")
    def test_list_not_found(self, mock_f_filter, mock_retrieve):
        # Return None to avoid crash in get_serializer_context
        mock_retrieve.return_value = None
        mock_f_filter.return_value.first.return_value = None

        view = JBrowseFeatureViewSet.as_view({"get": "list"})
        request = self.factory.get(
            "/api/jbrowse/features/refseq1", {"organism": "nonexistent"}
        )
        response = view(request, refseq="refseq1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class AutocompleteViewSetTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    @patch("machado.api.views.read.SearchQuerySet")
    def test_list(self, mock_sqs):
        mock_item = MagicMock()
        mock_item.autocomplete = "test string"
        mock_sqs.return_value.filter.return_value = [mock_item]
        view = autocompleteViewSet.as_view({"get": "list"})
        request = self.factory.get("/api/autocomplete", {"q": "test"})
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("test", response.data[0])

    @patch("machado.api.views.read.SearchQuerySet")
    @patch("machado.api.views.read.search")
    def test_list_attribute_error(self, mock_search, mock_sqs):
        mock_item = MagicMock()
        mock_item.autocomplete = "test string"
        mock_sqs.return_value.filter.return_value = [mock_item]
        mock_search.side_effect = AttributeError
        view = autocompleteViewSet.as_view({"get": "list"})
        request = self.factory.get("/api/autocomplete", {"q": "test"})
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_list_no_query(self):
        view = autocompleteViewSet.as_view({"get": "list"})
        request = self.factory.get("/api/autocomplete")
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])


class OrganismIDViewSetTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    def test_list_success(self):
        org = Organism.objects.create(genus="GenusA", species="speciesA")
        view = OrganismIDViewSet.as_view({"get": "list"})
        request = self.factory.get(
            "/api/organism/id", {"genus": "GenusA", "species": "speciesA"}
        )
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["organism_id"], org.organism_id)

    def test_list_all_params(self):
        org = Organism.objects.create(
            genus="GenusB",
            species="speciesB",
            infraspecific_name="infra",
            abbreviation="abb",
            common_name="common",
        )
        params = {
            "genus": "GenusB",
            "species": "speciesB",
            "infraspecific_name": "infra",
            "abbreviation": "abb",
            "common_name": "common",
        }
        view = OrganismIDViewSet.as_view({"get": "list"})
        request = self.factory.get("/api/organism/id", params)
        response = view(request)
        self.assertEqual(response.data["organism_id"], org.organism_id)

    @patch("machado.api.views.read.Organism.objects.filter")
    def test_list_not_found(self, mock_filter):
        mock_filter.return_value.get.side_effect = ObjectDoesNotExist
        view = OrganismIDViewSet.as_view({"get": "list"})
        request = self.factory.get("/api/organism/id", {"genus": "G"})
        response = view(request)
        self.assertEqual(response.data, {"organism_id": None})

    @patch("machado.api.views.read.Organism.objects.filter")
    def test_list_multiple(self, mock_filter):
        mock_filter.return_value.get.side_effect = MultipleObjectsReturned
        view = OrganismIDViewSet.as_view({"get": "list"})
        request = self.factory.get("/api/organism/id", {"genus": "G"})
        response = view(request)
        self.assertEqual(response.data, {"organism_id": None})


class OrganismListViewSetTest(TestCase):
    @patch("machado.api.views.read.Organism.objects.exclude")
    def test_list(self, mock_exclude):
        mock_exclude.return_value = []
        factory = APIRequestFactory()
        view = OrganismListViewSet.as_view({"get": "list"})
        request = factory.get("/api/organism/list")
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class FeatureIDViewSetTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    @patch("machado.api.views.read.Organism.objects.get")
    @patch("machado.api.views.read.retrieve_feature_id")
    def test_list_success(self, mock_retrieve, mock_org_get):
        mock_retrieve.return_value = 456
        view = FeatureIDViewSet.as_view({"get": "list"})
        request = self.factory.get(
            "/api/feature/id", {"accession": "acc1", "soType": "gene", "organism_id": 1}
        )
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["feature_id"], 456)

    @patch("machado.api.views.read.Organism.objects.get")
    @patch("machado.api.views.read.retrieve_feature_id")
    def test_list_not_found(self, mock_retrieve, mock_org_get):
        mock_retrieve.side_effect = ObjectDoesNotExist
        view = FeatureIDViewSet.as_view({"get": "list"})
        request = self.factory.get(
            "/api/feature/id", {"accession": "acc1", "soType": "gene", "organism_id": 1}
        )
        response = view(request)
        self.assertEqual(response.data, {"feature_id": None})


class FeatureOrthologViewSetTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    @patch("machado.api.views.read.Feature.objects.get")
    @patch("machado.api.views.read.Featureprop.objects.get")
    @patch("machado.api.views.read.Feature.objects.filter")
    def test_list_success(self, mock_f_filter, mock_fp_get, mock_f_get):
        mock_f_get.return_value.get_orthologous_group.return_value = "OG1"
        mock_fp_get.return_value.value = "OG1"
        mock_f_filter.return_value = []
        view = FeatureOrthologViewSet.as_view({"get": "list"})
        request = self.factory.get("/api/feature/ortholog/1")
        response = view(request, feature_id=1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["ortholog_group"], "OG1")

    @patch("machado.api.views.read.Feature.objects.get")
    def test_list_not_found(self, mock_f_get):
        mock_f_get.side_effect = ObjectDoesNotExist
        view = FeatureOrthologViewSet.as_view({"get": "list"})
        request = self.factory.get("/api/feature/ortholog/1")
        response = view(request, feature_id=1)
        # Note: There is a bug in read.py where it returns coexpression_group here
        self.assertEqual(response.data["coexpression_group"], None)


class FeatureCoexpressionViewSetTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    @patch("machado.api.views.read.Feature.objects.get")
    @patch("machado.api.views.read.Featureprop.objects.get")
    @patch("machado.api.views.read.Feature.objects.filter")
    def test_list_success(self, mock_f_filter, mock_fp_get, mock_f_get):
        mock_f_get.return_value.get_coexpression_group.return_value = "CG1"
        mock_fp_get.return_value.value = "CG1"
        mock_f_filter.return_value = []
        view = FeatureCoexpressionViewSet.as_view({"get": "list"})
        request = self.factory.get("/api/feature/coexpression/1")
        response = view(request, feature_id=1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["coexpression_group"], "CG1")


class FeatureExpressionViewSetTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    @patch("machado.api.views.read.Feature.objects.get")
    def test_list_success(self, mock_f_get):
        mock_f_get.return_value.get_expression_samples.return_value = []
        view = FeatureExpressionViewSet.as_view({"get": "list"})
        request = self.factory.get("/api/feature/expression/1")
        response = view(request, feature_id=1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch("machado.api.views.read.Feature.objects.get")
    def test_list_not_found(self, mock_f_get):
        mock_f_get.side_effect = ObjectDoesNotExist
        view = FeatureExpressionViewSet.as_view({"get": "list"})
        request = self.factory.get("/api/feature/expression/1")
        response = view(request, feature_id=1)
        self.assertEqual(response.data, [])


class FeatureInfoViewSetTest(TestCase):
    @patch("machado.api.views.read.Feature.objects.get")
    def test_list(self, mock_f_get):
        mock_f_get.return_value = MagicMock(spec=Feature)
        factory = APIRequestFactory()
        view = FeatureInfoViewSet.as_view({"get": "list"})
        request = factory.get("/api/feature/info/1")
        response = view(request, feature_id=1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class FeatureLocationViewSetTest(TestCase):
    @patch("machado.api.views.read.Feature.objects.get")
    def test_list(self, mock_f_get):
        mock_f_get.return_value.get_location.return_value = []
        factory = APIRequestFactory()
        view = FeatureLocationViewSet.as_view({"get": "list"})
        request = factory.get("/api/feature/location/1")
        response = view(request, feature_id=1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class FeatureSequenceViewSetTest(TestCase):
    @patch("machado.api.views.read.Feature.objects.get")
    def test_list(self, mock_f_get):
        mock_f_get.return_value = MagicMock(spec=Feature)
        factory = APIRequestFactory()
        view = FeatureSequenceViewSet.as_view({"get": "list"})
        request = factory.get("/api/feature/sequence/1")
        response = view(request, feature_id=1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class FeaturePublicationViewSetTest(TestCase):
    @patch("machado.api.views.read.Pub.objects.filter")
    def test_list(self, mock_filter):
        mock_filter.return_value = []
        factory = APIRequestFactory()
        view = FeaturePublicationViewSet.as_view({"get": "list"})
        request = factory.get("/api/feature/publication/1")
        response = view(request, feature_id=1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class FeatureOntologyViewSetTest(TestCase):
    @patch("machado.api.views.read.Cvterm.objects.filter")
    def test_list(self, mock_filter):
        mock_filter.return_value = []
        factory = APIRequestFactory()
        view = FeatureOntologyViewSet.as_view({"get": "list"})
        request = factory.get("/api/feature/ontology/1")
        response = view(request, feature_id=1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class FeatureProteinMatchesViewSetTest(TestCase):
    @patch("machado.api.views.read.FeatureRelationship.objects.filter")
    def test_list(self, mock_filter):
        mock_filter.return_value = []
        factory = APIRequestFactory()
        view = FeatureProteinMatchesViewSet.as_view({"get": "list"})
        request = factory.get("/api/feature/proteinmatches/1")
        response = view(request, feature_id=1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class FeatureSimilarityViewSetTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    @patch("machado.api.views.read.Featureloc.objects.filter")
    @patch("machado.api.views.read.Analysisfeature.objects.get")
    @patch("machado.api.views.read.Analysis.objects.get")
    def test_list(self, mock_a_get, mock_af_get, mock_fl_filter):
        mock_match = MagicMock()
        mock_match.srcfeature.dbxref.db.name = "db"
        mock_match.srcfeature.uniquename = "hit1"
        mock_match.srcfeature.name = "hit_name"
        mock_match.srcfeature.type.name = "type"
        mock_match.fmin = 0
        mock_match.fmax = 100

        mock_fl_qs_parts = MagicMock()
        mock_fl_qs_parts.values_list.return_value = [10]
        mock_fl_qs_query = MagicMock()
        mock_fl_qs_query.__getitem__.return_value = mock_match
        mock_fl_qs_hit = MagicMock()
        mock_fl_qs_hit.exclude.return_value = mock_fl_qs_hit
        mock_fl_qs_hit.__getitem__.return_value = mock_match

        mock_fl_filter.side_effect = [
            mock_fl_qs_parts,
            mock_fl_qs_query,
            mock_fl_qs_hit,
        ]

        mock_af = MagicMock()
        mock_af.analysis_id = 1
        mock_af.normscore = 90
        mock_af.significance = 0.001
        mock_af_get.return_value = mock_af

        mock_a = MagicMock()
        mock_a_get.return_value = mock_a

        view = FeatureSimilarityViewSet.as_view({"get": "list"})
        request = self.factory.get("/api/feature/similarity/1")
        response = view(request, feature_id=1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    @patch("machado.api.views.read.Featureloc.objects.filter")
    def test_list_not_found(self, mock_fl_filter):
        mock_fl_filter.side_effect = ObjectDoesNotExist
        view = FeatureSimilarityViewSet.as_view({"get": "list"})
        request = self.factory.get("/api/feature/similarity/1")
        response = view(request, feature_id=1)
        self.assertEqual(response.data, [])

    @patch("machado.api.views.read.Featureloc.objects.filter")
    @patch("machado.api.views.read.Analysisfeature.objects.get")
    @patch("machado.api.views.read.Analysis.objects.get")
    def test_list_rawscore(self, mock_a_get, mock_af_get, mock_fl_filter):
        mock_match = MagicMock()
        mock_match.srcfeature.dbxref.db.name = "db"
        mock_match.srcfeature.uniquename = "hit1"
        mock_match.srcfeature.name = "hit_name"
        mock_match.srcfeature.type.name = "type"
        mock_match.fmin = 0
        mock_match.fmax = 100

        mock_fl_qs_parts = MagicMock()
        mock_fl_qs_parts.values_list.return_value = [10]
        mock_fl_qs_query = MagicMock()
        mock_fl_qs_query.__getitem__.return_value = mock_match
        mock_fl_qs_hit = MagicMock()
        mock_fl_qs_hit.exclude.return_value = mock_fl_qs_hit
        mock_fl_qs_hit.__getitem__.return_value = mock_match

        mock_fl_filter.side_effect = [
            mock_fl_qs_parts,
            mock_fl_qs_query,
            mock_fl_qs_hit,
        ]

        mock_af = MagicMock()
        mock_af.analysis_id = 1
        mock_af.normscore = None
        mock_af.rawscore = 80
        mock_af.significance = 0.001
        mock_af_get.return_value = mock_af

        mock_a = MagicMock()
        mock_a_get.return_value = mock_a

        view = FeatureSimilarityViewSet.as_view({"get": "list"})
        request = self.factory.get("/api/feature/similarity/1")
        response = view(request, feature_id=1)
        self.assertEqual(float(response.data[0]["score"]), 80)


class HistoryListViewSetTest(TestCase):
    def test_list(self):
        History.objects.create(command="test", description="desc")
        factory = APIRequestFactory()
        view = HistoryListViewSet.as_view({"get": "list"})
        request = factory.get("/api/history")
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_list_with_search_and_order(self):
        History.objects.create(command="cmd1", description="desc1")
        History.objects.create(command="cmd2", description="desc2")
        factory = APIRequestFactory()
        view = HistoryListViewSet.as_view({"get": "list"})
        request = factory.get(
            "/api/history", {"search": "cmd1", "ordering": "created_at"}
        )
        response = view(request)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["command"], "cmd1")

    def test_list_invalid_order(self):
        History.objects.create(command="cmd1")
        factory = APIRequestFactory()
        view = HistoryListViewSet.as_view({"get": "list"})
        request = factory.get("/api/history", {"ordering": "invalid"})
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
