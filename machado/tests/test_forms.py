"""Module tests."""

from django.test import TestCase
from django.http import QueryDict
from unittest.mock import MagicMock, patch

from machado.forms import FeatureSearchForm
from django.contrib.postgres.search import SearchQuery


class FeatureSearchFormTest(TestCase):
    """Test suite for FeatureSearchForm."""

    def test_search_invalid(self):
        """Test search invalid."""
        form = FeatureSearchForm(data={})
        # Mock is_valid since we are just testing search logic
        form.is_valid = MagicMock(return_value=False)
        form.cleaned_data = {}

        # The real form returns FeatureSearchIndex.objects.none() if invalid,
        # but the view does the is_valid check.
        # If we just call search directly with an empty/invalid form, it applies an empty 'q'
        with patch(
            "machado.forms.FeatureSearchIndex.objects.select_related"
        ) as mock_select:
            mock_qs = MagicMock()
            mock_select.return_value.all.return_value = mock_qs
            result = form.search()
            self.assertEqual(result, mock_qs)

    def test_search_empty_q(self):
        """Test search empty q."""
        data = QueryDict(mutable=True)
        data.update({"q": ""})

        form = FeatureSearchForm(data=data)
        form.is_valid = MagicMock(return_value=True)
        form.cleaned_data = {"q": ""}

        with patch(
            "machado.forms.FeatureSearchIndex.objects.select_related"
        ) as mock_select:
            mock_qs = MagicMock()
            mock_select.return_value.all.return_value = mock_qs

            result = form.search()
            self.assertEqual(result, mock_qs)

    def test_search_with_q(self):
        """Test search with q."""
        data = QueryDict(mutable=True)
        data.update({"q": "test"})

        form = FeatureSearchForm(data=data)
        form.is_valid = MagicMock(return_value=True)
        form.cleaned_data = {"q": "test"}

        with patch(
            "machado.forms.FeatureSearchIndex.objects.select_related"
        ) as mock_select:
            mock_qs = MagicMock()
            mock_select.return_value.all.return_value = mock_qs
            mock_qs.filter.return_value.annotate.return_value = "annotated_qs"

            result = form.search()
            self.assertEqual(result, "annotated_qs")

            # verify it filters by search_vector
            filter_kwargs = mock_qs.filter.call_args[1]
            self.assertIn("search_vector", filter_kwargs)
            self.assertIsInstance(filter_kwargs["search_vector"], SearchQuery)

    def test_search_with_facets(self):
        """Test search with facets."""
        data = QueryDict(mutable=True)
        data.update({"q": "test"})
        # selected_facets is passed via method arg in new design, not via POST data
        selected_facets = ["analyses:A", "analyses:B", "so_term:C", "so_term:D"]

        form = FeatureSearchForm(data=data)
        form.is_valid = MagicMock(return_value=True)
        form.cleaned_data = {"q": "test"}

        with patch(
            "machado.forms.FeatureSearchIndex.objects.select_related"
        ) as mock_select:
            mock_qs = MagicMock()
            mock_select.return_value.all.return_value = mock_qs

            # Mocks for facet chaining
            mock_qs.filter.return_value = mock_qs
            mock_qs.annotate.return_value = "final_qs"

            result = form.search(selected_facets=selected_facets)
            self.assertEqual(result, "final_qs")

            # sqs.filter should have been called multiple times
            self.assertTrue(mock_qs.filter.called)
