# Copyright 2018 by Embrapa.  All rights reserved.
#
# This code is part of the machado distribution and governed by its
# license. Please see the LICENSE.txt and README.md files that should
# have been included as part of this package for licensing information.

"""Tests feature view."""

from django.test import TestCase, RequestFactory

from machado.templatetags import machado_extras


class MachadoExtrasTest(TestCase):
    """Tests Feature View."""

    def setUp(self):
        """Set up."""
        self.factory = RequestFactory()

    def test_param_replace(self):
        """Tests - param_replace."""
        request = self.factory.get("/find/?q=&page=1")
        context = {"request": request}
        result = machado_extras.param_replace(context, page=2)
        self.assertEqual("q=&page=2", result)

        request = self.factory.get("/find/?q=&selected_facets=so_term_exact:gene")
        context = {"request": request}
        result = machado_extras.param_replace(
            context, selected_facets="organism:Arabidopsis thaliana"
        )
        self.assertEqual(
            "q=&selected_facets=so_term_exact%3Agene&"
            "selected_facets=organism%3AArabidopsis+thaliana",
            result,
        )

    def test_remove_facet(self):
        """Tests - test_remove_facet."""
        request = self.factory.get(
            "/find/?q=&selected_facets=so_term_exact:gene&"
            "selected_facets=organism:Arabidopsis thaliana"
        )
        context = {"request": request}
        machado_extras.remove_facet(context, "organism")

    def test_param_replace_order_by(self):
        """Tests - param_replace order_by."""
        request = self.factory.get("/find/?q=&order_by=name")
        context = {"request": request}
        result = machado_extras.param_replace(context, order_by="name")
        self.assertEqual("q=&order_by=-name", result)

        result = machado_extras.param_replace(context, order_by="type")
        self.assertEqual("q=&order_by=type", result)

    def test_remove_query(self):
        """Tests - remove_query."""
        request = self.factory.get("/find/?q=test&page=1")
        context = {"request": request}
        result = machado_extras.remove_query(context)
        self.assertEqual("page=1", result)

    def test_remove_facet_field(self):
        """Tests - remove_facet_field."""
        request = self.factory.get(
            "/find/?q=&selected_facets=so_term_exact:gene&"
            "selected_facets=organism:Arabidopsis thaliana"
        )
        context = {"request": request}
        result = machado_extras.remove_facet_field(
            context, "organism:Arabidopsis thaliana"
        )
        self.assertEqual("q=&selected_facets=so_term_exact%3Agene", result)

    def test_get_item(self):
        """Tests - get_item."""
        data = {"key1": "value1"}
        self.assertEqual("value1", machado_extras.get_item(data, "key1"))

    def test_get_count(self):
        """Tests - get_count."""
        data = {"key1": [1, 2, 3]}
        self.assertEqual(3, machado_extras.get_count(data, "key1"))

    def test_split(self):
        """Tests - split."""
        self.assertEqual(["a", "b"], machado_extras.split("a,b", ","))
