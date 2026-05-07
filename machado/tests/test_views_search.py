"""Tests for search views."""

from django.test import TestCase, RequestFactory
from machado.views.search import FeatureSearchView, FeatureSearchExportView
from unittest.mock import patch, MagicMock


class SearchViewsTest(TestCase):
    """Test suite for search-related views."""

    def setUp(self):
        """Set up the test case with a request factory."""
        self.factory = RequestFactory()

    @patch("machado.views.search.FacetedSearchView.get_queryset")
    def test_feature_search_view_get_queryset(self, mock_super_get_qs):
        """Test get_queryset of FeatureSearchView with pagination and ordering."""
        mock_qs = MagicMock()
        mock_sqs_facets = MagicMock()
        mock_qs.facet.return_value = mock_sqs_facets
        mock_sqs_facets.order_by.return_value = mock_qs
        mock_super_get_qs.return_value = mock_qs

        request = self.factory.get("/find/?q=test&order_by=name&records=10")
        view = FeatureSearchView()
        view.request = request

        view.get_queryset()

        # Verify pagination and order_by
        self.assertEqual(view.paginate_by, "10")
        self.assertTrue(mock_qs.facet.called)

    @patch("machado.views.search.FacetedSearchView.get_queryset")
    def test_feature_search_view_get_queryset_defaults(
        self, mock_super_get_qs
    ):
        """Test get_queryset of FeatureSearchView with default values."""
        mock_qs = MagicMock()
        mock_sqs_facets = MagicMock()
        mock_qs.facet.return_value = mock_sqs_facets
        mock_sqs_facets.order_by.return_value = mock_qs
        mock_super_get_qs.return_value = mock_qs

        request = self.factory.get("/find/")
        view = FeatureSearchView()
        view.request = request

        view.get_queryset()

        self.assertEqual(view.paginate_by, 50)
        self.assertTrue(mock_qs.facet.called)

    @patch("machado.views.search.FacetedSearchView.get_context_data")
    def test_feature_search_view_get_context_data(
        self, mock_super_get_context
    ):
        """Test context data preparation in FeatureSearchView."""
        mock_super_get_context.return_value = {}

        view = FeatureSearchView()
        view.get_form_kwargs = MagicMock(
            return_value={"selected_facets": ["so_term:gene", "other:val"]}
        )

        context = view.get_context_data()

        self.assertEqual(context["so_term_count"], 1)
        self.assertIn("so_term", context["selected_facets_fields"])
        self.assertIn("other", context["selected_facets_fields"])

    @patch("machado.views.search.FacetedSearchView.get_context_data")
    def test_feature_search_export_view_get_context_data(
        self, mock_super_get_context
    ):
        """Test context data preparation in FeatureSearchExportView."""
        mock_super_get_context.return_value = {}

        view = FeatureSearchExportView()
        view.get_form_kwargs = MagicMock(
            return_value={"data": {"export": "fasta"}, "selected_facets": []}
        )

        context = view.get_context_data()
        self.assertEqual(context["file_format"], "fasta")
        self.assertEqual(view.file_format, "fasta")

    @patch("machado.views.search.FacetedSearchView.get_context_data")
    def test_feature_search_export_view_get_context_data_default(
        self, mock_super_get_context
    ):
        """Test default context data in FeatureSearchExportView."""
        mock_super_get_context.return_value = {}

        view = FeatureSearchExportView()
        view.get_form_kwargs = MagicMock(
            return_value={"data": {}, "selected_facets": []}
        )

        context = view.get_context_data()
        self.assertEqual(context["file_format"], "tsv")

    @patch("machado.views.search.FacetedSearchView.dispatch")
    def test_feature_search_export_view_dispatch(self, mock_super_dispatch):
        """Test dispatch method of FeatureSearchExportView."""
        mock_response = {}
        mock_super_dispatch.return_value = mock_response

        view = FeatureSearchExportView()
        view.file_format = "fasta"

        request = self.factory.get("/export/")
        response = view.dispatch(request)

        self.assertEqual(
            response["Content-Disposition"],
            'attachment; filename="machado_search_results.fasta"',
        )
