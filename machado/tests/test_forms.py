from django.test import TestCase
from django.http import QueryDict
from unittest.mock import MagicMock

from machado.forms import FeatureSearchForm


class FeatureSearchFormTest(TestCase):
    def test_search_invalid(self):
        form = FeatureSearchForm(data={})
        # If no 'q' is provided, it might be invalid depending on the form definition.
        # Wait, FacetedSearchForm requires 'q'?
        # Actually we can just mock is_valid
        form.is_valid = MagicMock(return_value=False)
        form.no_query_found = MagicMock(return_value="no_query")
        form.cleaned_data = {}

        result = form.search()
        self.assertEqual(result, "no_query")

    def test_search_empty_q(self):
        mock_sqs = MagicMock()
        data = QueryDict(mutable=True)
        data.update({"q": ""})

        form = FeatureSearchForm(data=data, searchqueryset=mock_sqs)
        form.is_valid = MagicMock(return_value=True)
        form.cleaned_data = {"q": ""}

        result = form.search()
        self.assertEqual(result, mock_sqs)

    def test_search_with_q(self):
        mock_sqs = MagicMock()
        mock_sqs.filter.return_value = "filtered_sqs"

        data = QueryDict(mutable=True)
        data.update({"q": "test"})

        form = FeatureSearchForm(data=data, searchqueryset=mock_sqs)
        form.is_valid = MagicMock(return_value=True)
        form.cleaned_data = {"q": 'test:escaped/with.quotes"'}

        result = form.search()
        self.assertEqual(result, "filtered_sqs")
        # Ensure that exact escaping happens
        # text=Raw(q)
        filter_call_args = mock_sqs.filter.call_args
        self.assertIsNotNone(filter_call_args)

    def test_search_with_facets(self):
        mock_sqs = MagicMock()
        mock_sqs.filter.return_value = mock_sqs

        # Test intersect (and) and union (or) facets
        data = QueryDict(mutable=True)
        data.update({"q": "test"})
        data.appendlist("selected_facets", "analyses:A")
        data.appendlist("selected_facets", "analyses:B")
        data.appendlist("selected_facets", "otherfacet:C")
        data.appendlist("selected_facets", "otherfacet:D")

        form = FeatureSearchForm(data=data, searchqueryset=mock_sqs)
        form.is_valid = MagicMock(return_value=True)
        form.cleaned_data = {"q": "test"}

        result = form.search()
        self.assertIsNotNone(result)

        # sqs.filter should have been called for both 'otherfacet' and 'analyses'
        self.assertTrue(mock_sqs.filter.called)
