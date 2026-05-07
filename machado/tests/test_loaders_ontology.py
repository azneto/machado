# Copyright 2018 by Embrapa.  All rights reserved.
#
# This code is part of the machado distribution and governed by its
# license. Please see the LICENSE.txt and README.md files that should
# have been included as part of this package for licensing information.

"""Tests for ontology loader."""

from django.test import TestCase
from machado.loaders.ontology import OntologyLoader
from machado.loaders.exceptions import ImportingError
from machado.models import (
    Cvterm,
    Cvtermprop,
    CvtermDbxref,
    Cvtermsynonym,
    CvtermRelationship,
)


class OntologyLoaderTest(TestCase):
    def setUp(self):
        self.loader = OntologyLoader(cv_name="sequence", cv_definition="SO definition")

    def test_init_already_exists(self):
        with self.assertRaisesRegex(ImportingError, "already registered"):
            OntologyLoader(cv_name="sequence")

    def test_store_type_def(self):
        typedef = {
            "id": "SO:part_of",
            "name": "part of",
            "def": "a relationship",
            "comment": ["comment1"],
            "is_class_level": True,
            "is_metadata_tag": True,
            "is_symmetric": True,
            "is_transitive": True,
            "xref": ["REF:123"],
        }
        self.loader.store_type_def(typedef)

        cvterm = Cvterm.objects.get(name="part of")
        self.assertEqual(cvterm.dbxref.db.name, "SO")
        self.assertEqual(cvterm.definition, "a relationship")
        self.assertEqual(cvterm.is_relationshiptype, 1)

        # Check props
        self.assertTrue(
            Cvtermprop.objects.filter(
                cvterm=cvterm, type__name="comment", value="comment1"
            ).exists()
        )
        self.assertTrue(
            Cvtermprop.objects.filter(
                cvterm=cvterm, type__name="is_class_level", value="1"
            ).exists()
        )
        self.assertTrue(
            Cvtermprop.objects.filter(
                cvterm=cvterm, type__name="is_metadata_tag", value="1"
            ).exists()
        )
        self.assertTrue(
            Cvtermprop.objects.filter(
                cvterm=cvterm, type__name="is_symmetric", value="1"
            ).exists()
        )
        self.assertTrue(
            Cvtermprop.objects.filter(
                cvterm=cvterm, type__name="is_transitive", value="1"
            ).exists()
        )

        # Check xref
        self.assertTrue(
            CvtermDbxref.objects.filter(
                cvterm=cvterm, dbxref__db__name="REF", dbxref__accession="123"
            ).exists()
        )

    def test_store_type_def_no_prefix(self):
        typedef = {"id": "rel1"}
        self.loader.store_type_def(typedef)
        cvterm = Cvterm.objects.get(name="rel1")
        self.assertEqual(cvterm.dbxref.db.name, "_global")

    def test_store_term(self):
        data = {
            "name": "gene",
            "namespace": "sequence",
            "def": '"A DNA fragment" [REF:456]',
            "alt_id": ["SO:0000704"],
            "comment": "a comment",
            "xref": ["XREF:789"],
            "synonym": ['"syn1" EXACT []'],
        }
        self.loader.store_term("SO:0000704", data)

        cvterm = Cvterm.objects.get(name="gene", dbxref__accession="0000704")
        self.assertEqual(cvterm.definition, "A DNA fragment")

        # Check alt_id
        self.assertTrue(
            CvtermDbxref.objects.filter(
                cvterm=cvterm,
                dbxref__db__name="SO",
                dbxref__accession="0000704",
                is_for_definition=0,
            ).exists()
        )

        # Check comment
        self.assertTrue(
            Cvtermprop.objects.filter(
                cvterm=cvterm, type__name="comment", value="a comment"
            ).exists()
        )

        # Check xref
        self.assertTrue(
            CvtermDbxref.objects.filter(
                cvterm=cvterm, dbxref__db__name="XREF", dbxref__accession="789"
            ).exists()
        )

        # Check synonym
        self.assertTrue(
            Cvtermsynonym.objects.filter(cvterm=cvterm, synonym="syn1").exists()
        )

    def test_store_relationship(self):
        # Create terms first
        self.loader.store_term("SO:0001", {"name": "gene"})
        self.loader.store_term("SO:0002", {"name": "coding_gene"})

        # Create custom relationship type
        self.loader.store_type_def({"id": "part_of", "name": "part_of"})

        # Store relationships
        self.loader.store_relationship("SO:0002", "SO:0001", "is_a")
        self.loader.store_relationship("SO:0002", "SO:0001", "part_of")

        gene = Cvterm.objects.get(name="gene")
        coding = Cvterm.objects.get(name="coding_gene")
        is_a = Cvterm.objects.get(name="is_a")
        part_of = Cvterm.objects.get(name="part_of")

        self.assertTrue(
            CvtermRelationship.objects.filter(
                subject=coding, object=gene, type=is_a
            ).exists()
        )
        self.assertTrue(
            CvtermRelationship.objects.filter(
                subject=coding, object=gene, type=part_of
            ).exists()
        )

    def test_process_cvterm_go_synonym(self):
        cvterm = Cvterm.objects.get(name="is_a")  # reuse any
        self.loader.process_cvterm_go_synonym(
            cvterm, '"assembly" [GOC:123]', "EXACT_synonym"
        )
        self.assertTrue(
            Cvtermsynonym.objects.filter(
                cvterm=cvterm, synonym="assembly", type__name="exact"
            ).exists()
        )

    def test_process_cvterm_def_edge_cases(self):
        cvterm = Cvterm.objects.get(name="is_a")
        # No dbxrefs
        self.loader.process_cvterm_def(cvterm, "Simple definition")
        self.assertEqual(cvterm.definition, "Simple definition")

        # URL dbxref
        self.loader.process_cvterm_def(cvterm, '"Def" [http://example.com]')
        self.assertTrue(
            CvtermDbxref.objects.filter(cvterm=cvterm, dbxref__db__name="URL").exists()
        )
