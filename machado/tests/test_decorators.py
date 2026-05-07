# Copyright 2018 by Embrapa.  All rights reserved.
#
# This code is part of the machado distribution and governed by its
# license. Please see the LICENSE.txt and README.md files that should
# have been included as part of this package for licensing information.

"""Tests for machado.decorators."""

from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase, override_settings
from unittest.mock import MagicMock

from machado.decorators import (
    get_feature_dbxrefs,
    get_feature_product,
    get_feature_description,
    get_feature_note,
    get_feature_annotation,
    get_feature_doi,
    get_feature_display,
    get_feature_properties,
    get_feature_synonyms,
    get_feature_orthologous_group,
    get_feature_coexpression_group,
    get_feature_expression_samples,
    get_feature_relationship,
    get_feature_cvterm,
    get_feature_location,
    machado_feature_methods,
    get_pub_authors,
    get_pub_doi,
    machado_pub_methods,
)


class GetFeatureDbxrefsTest(TestCase):
    """Tests for get_feature_dbxrefs."""

    def test_with_url(self):
        mock_dbxref = MagicMock()
        mock_dbxref.dbxref.db.url = "www.example.com/"
        mock_dbxref.dbxref.db.urlprefix = "https"
        mock_dbxref.dbxref.accession = "12345"
        mock_dbxref.dbxref.db.name = "TestDB"

        mock_self = MagicMock()
        mock_self.FeatureDbxref_feature_Feature.all.return_value = [mock_dbxref]

        result = get_feature_dbxrefs(mock_self)
        self.assertEqual(len(result), 1)
        self.assertIn("TestDB:12345", result[0])
        self.assertIn("href='https://www.example.com/12345'", result[0])

    def test_without_url(self):
        mock_dbxref = MagicMock()
        mock_dbxref.dbxref.db.url = None
        mock_dbxref.dbxref.db.name = "LocalDB"
        mock_dbxref.dbxref.accession = "67890"

        mock_self = MagicMock()
        mock_self.FeatureDbxref_feature_Feature.all.return_value = [mock_dbxref]

        result = get_feature_dbxrefs(mock_self)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], "LocalDB:67890")

    def test_empty(self):
        mock_self = MagicMock()
        mock_self.FeatureDbxref_feature_Feature.all.return_value = []

        result = get_feature_dbxrefs(mock_self)
        self.assertEqual(result, [])


class GetFeaturePropTest(TestCase):
    """Tests for get_feature_product, get_feature_description, get_feature_note."""

    def test_product_found(self):
        mock_self = MagicMock()
        mock_self.Featureprop_feature_Feature.get.return_value.value = "some product"
        result = get_feature_product(mock_self)
        self.assertEqual(result, "some product")

    def test_product_not_found(self):
        mock_self = MagicMock()
        mock_self.Featureprop_feature_Feature.get.side_effect = ObjectDoesNotExist
        result = get_feature_product(mock_self)
        self.assertIsNone(result)

    def test_description_found(self):
        mock_self = MagicMock()
        mock_self.Featureprop_feature_Feature.get.return_value.value = "some desc"
        result = get_feature_description(mock_self)
        self.assertEqual(result, "some desc")

    def test_description_not_found(self):
        mock_self = MagicMock()
        mock_self.Featureprop_feature_Feature.get.side_effect = ObjectDoesNotExist
        result = get_feature_description(mock_self)
        self.assertIsNone(result)

    def test_note_found(self):
        mock_self = MagicMock()
        mock_self.Featureprop_feature_Feature.get.return_value.value = "some note"
        result = get_feature_note(mock_self)
        self.assertEqual(result, "some note")

    def test_note_not_found(self):
        mock_self = MagicMock()
        mock_self.Featureprop_feature_Feature.get.side_effect = ObjectDoesNotExist
        result = get_feature_note(mock_self)
        self.assertIsNone(result)


class GetFeatureAnnotationTest(TestCase):
    """Tests for get_feature_annotation."""

    def test_annotation_with_doi(self):
        mock_fp = MagicMock()
        mock_fp.value = "Annotation text"
        mock_fp.FeaturepropPub_featureprop_Featureprop.get.return_value.pub.get_doi.return_value = (
            "10.1234/test"
        )

        mock_self = MagicMock()
        mock_self.Featureprop_feature_Feature.filter.return_value = [mock_fp]

        result = get_feature_annotation(mock_self)
        self.assertEqual(len(result), 1)
        self.assertIn("DOI:10.1234/test", result[0])

    def test_annotation_without_doi(self):
        mock_fp = MagicMock()
        mock_fp.value = "Annotation text"
        mock_fp.FeaturepropPub_featureprop_Featureprop.get.side_effect = (
            ObjectDoesNotExist
        )

        mock_self = MagicMock()
        mock_self.Featureprop_feature_Feature.filter.return_value = [mock_fp]

        result = get_feature_annotation(mock_self)
        self.assertEqual(result, ["Annotation text"])

    def test_annotation_not_found(self):
        mock_self = MagicMock()
        mock_self.Featureprop_feature_Feature.filter.side_effect = ObjectDoesNotExist

        result = get_feature_annotation(mock_self)
        self.assertIsNone(result)


class GetFeatureDoiTest(TestCase):
    """Tests for get_feature_doi."""

    def test_doi_from_pubs_and_annotations(self):
        mock_featurepub = MagicMock()
        mock_featurepub.pub.get_doi.return_value = "10.1234/pub"

        mock_fp = MagicMock()
        mock_fp.FeaturepropPub_featureprop_Featureprop.get.return_value.pub.get_doi.return_value = (
            "10.1234/annot"
        )

        mock_self = MagicMock()
        mock_self.FeaturePub_feature_Feature.filter.return_value = [mock_featurepub]
        mock_self.Featureprop_feature_Feature.filter.return_value = [mock_fp]

        result = get_feature_doi(mock_self)
        self.assertIn("10.1234/pub", result)
        self.assertIn("10.1234/annot", result)

    def test_doi_annotation_no_doi(self):
        mock_featurepub = MagicMock()
        mock_featurepub.pub.get_doi.return_value = "10.1234/pub"

        mock_fp = MagicMock()
        mock_fp.FeaturepropPub_featureprop_Featureprop.get.side_effect = (
            ObjectDoesNotExist
        )

        mock_self = MagicMock()
        mock_self.FeaturePub_feature_Feature.filter.return_value = [mock_featurepub]
        mock_self.Featureprop_feature_Feature.filter.return_value = [mock_fp]

        result = get_feature_doi(mock_self)
        self.assertIn("10.1234/pub", result)
        self.assertEqual(len(result), 1)

    def test_doi_filter_raises(self):
        mock_self = MagicMock()
        mock_self.FeaturePub_feature_Feature.filter.return_value = []
        mock_self.Featureprop_feature_Feature.filter.side_effect = ObjectDoesNotExist

        result = get_feature_doi(mock_self)
        self.assertIsNone(result)


class GetFeatureDisplayTest(TestCase):
    """Tests for get_feature_display."""

    def test_display_found(self):
        mock_self = MagicMock()
        mock_self.Featureprop_feature_Feature.get.return_value.value = "display text"
        result = get_feature_display(mock_self)
        self.assertEqual(result, "display text")

    def test_display_fallback_product(self):
        mock_self = MagicMock()
        mock_self.Featureprop_feature_Feature.get.side_effect = ObjectDoesNotExist
        mock_self.get_product.return_value = "product text"
        result = get_feature_display(mock_self)
        self.assertEqual(result, "product text")

    def test_display_fallback_description(self):
        mock_self = MagicMock()
        mock_self.Featureprop_feature_Feature.get.side_effect = ObjectDoesNotExist
        mock_self.get_product.return_value = None
        mock_self.get_description.return_value = "desc text"
        result = get_feature_display(mock_self)
        self.assertEqual(result, "desc text")

    def test_display_fallback_note(self):
        mock_self = MagicMock()
        mock_self.Featureprop_feature_Feature.get.side_effect = ObjectDoesNotExist
        mock_self.get_product.return_value = None
        mock_self.get_description.return_value = None
        mock_self.get_note.return_value = "note text"
        result = get_feature_display(mock_self)
        self.assertEqual(result, "note text")

    def test_display_fallback_none(self):
        mock_self = MagicMock()
        mock_self.Featureprop_feature_Feature.get.side_effect = ObjectDoesNotExist
        mock_self.get_product.return_value = None
        mock_self.get_description.return_value = None
        mock_self.get_note.return_value = None
        result = get_feature_display(mock_self)
        self.assertIsNone(result)


class GetFeaturePropertiesTest(TestCase):
    """Tests for get_feature_properties."""

    def test_properties_found(self):
        mock_qs = MagicMock()
        mock_qs.exclude.return_value.order_by.return_value.values_list.return_value = [
            ("product", "val1"),
            ("note", "val2"),
        ]
        mock_self = MagicMock()
        mock_self.Featureprop_feature_Feature.filter.return_value = mock_qs

        result = get_feature_properties(mock_self)
        self.assertEqual(len(result), 2)

    def test_properties_not_found(self):
        mock_self = MagicMock()
        mock_self.Featureprop_feature_Feature.filter.side_effect = ObjectDoesNotExist

        result = get_feature_properties(mock_self)
        self.assertEqual(result, [])


class GetFeatureSynonymsTest(TestCase):
    """Tests for get_feature_synonyms."""

    def test_synonyms(self):
        mock_syn = MagicMock()
        mock_syn.synonym.name = "SynonymA"

        mock_self = MagicMock()
        mock_self.FeatureSynonym_feature_Feature.all.return_value = [mock_syn]

        result = get_feature_synonyms(mock_self)
        self.assertEqual(result, ["SynonymA"])

    def test_no_synonyms(self):
        mock_self = MagicMock()
        mock_self.FeatureSynonym_feature_Feature.all.return_value = []

        result = get_feature_synonyms(mock_self)
        self.assertEqual(result, [])


class GetFeatureOrthologousGroupTest(TestCase):
    """Tests for get_feature_orthologous_group."""

    def test_found(self):
        mock_self = MagicMock()
        mock_self.Featureprop_feature_Feature.get.return_value.value = "OG001"
        result = get_feature_orthologous_group(mock_self)
        self.assertEqual(result, "OG001")

    def test_not_found(self):
        mock_self = MagicMock()
        mock_self.Featureprop_feature_Feature.get.side_effect = ObjectDoesNotExist
        result = get_feature_orthologous_group(mock_self)
        self.assertIsNone(result)


class GetFeatureCoexpressionGroupTest(TestCase):
    """Tests for get_feature_coexpression_group."""

    def test_found(self):
        mock_self = MagicMock()
        mock_self.Featureprop_feature_Feature.get.return_value.value = "CG001"
        result = get_feature_coexpression_group(mock_self)
        self.assertEqual(result, "CG001")

    def test_not_found(self):
        mock_self = MagicMock()
        mock_self.Featureprop_feature_Feature.get.side_effect = ObjectDoesNotExist
        result = get_feature_coexpression_group(mock_self)
        self.assertIsNone(result)


class GetFeatureExpressionSamplesTest(TestCase):
    """Tests for get_feature_expression_samples."""

    def test_samples_found(self):
        mock_qs = MagicMock()
        mock_qs.annotate.return_value = mock_qs
        mock_qs.filter.return_value = mock_qs
        mock_qs.exclude.return_value = mock_qs
        mock_qs.values.return_value = [{"analysis__sourcename": "A", "normscore": 1.0}]

        mock_self = MagicMock()
        mock_self.Analysisfeature_feature_Feature.annotate.return_value = mock_qs

        result = get_feature_expression_samples(mock_self)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)

    def test_samples_not_found(self):
        mock_self = MagicMock()
        mock_self.Analysisfeature_feature_Feature.annotate.side_effect = (
            ObjectDoesNotExist
        )

        result = get_feature_expression_samples(mock_self)
        self.assertIsNone(result)


class GetFeatureRelationshipTest(TestCase):
    """Tests for get_feature_relationship."""

    @override_settings(MACHADO_VALID_TYPES=["gene", "mRNA", "polypeptide"])
    def test_relationship_object_side(self):
        mock_subject = MagicMock()
        mock_subject.type.name = "gene"
        mock_rel = MagicMock()
        mock_rel.subject = mock_subject

        mock_self = MagicMock()
        mock_self.FeatureRelationship_object_Feature.filter.return_value = [mock_rel]
        mock_self.FeatureRelationship_subject_Feature.filter.return_value = []

        result = get_feature_relationship(mock_self)
        self.assertIn(mock_subject, result)

    @override_settings(MACHADO_VALID_TYPES=["gene", "mRNA", "polypeptide"])
    def test_relationship_subject_side(self):
        mock_object = MagicMock()
        mock_object.type.name = "mRNA"
        mock_rel = MagicMock()
        mock_rel.object = mock_object

        mock_self = MagicMock()
        mock_self.FeatureRelationship_object_Feature.filter.return_value = []
        mock_self.FeatureRelationship_subject_Feature.filter.return_value = [mock_rel]

        result = get_feature_relationship(mock_self)
        self.assertIn(mock_object, result)

    @override_settings(MACHADO_VALID_TYPES=["gene"])
    def test_relationship_filtered_by_valid_types(self):
        mock_subject = MagicMock()
        mock_subject.type.name = "CDS"  # Not in MACHADO_VALID_TYPES

        mock_rel = MagicMock()
        mock_rel.subject = mock_subject

        mock_self = MagicMock()
        mock_self.FeatureRelationship_object_Feature.filter.return_value = [mock_rel]
        mock_self.FeatureRelationship_subject_Feature.filter.return_value = []

        result = get_feature_relationship(mock_self)
        self.assertEqual(result, [])

    def test_relationship_no_valid_types_setting(self):
        mock_self = MagicMock()
        with self.settings():
            # Remove MACHADO_VALID_TYPES from settings
            from django.conf import settings

            if hasattr(settings, "MACHADO_VALID_TYPES"):
                delattr(settings, "MACHADO_VALID_TYPES")
            with self.assertRaises(AttributeError):
                get_feature_relationship(mock_self)


class GetFeatureCvtermTest(TestCase):
    """Tests for get_feature_cvterm."""

    def test_cvterm(self):
        mock_qs = MagicMock()
        mock_qs.values.return_value = [{"name": "gene", "cv": "sequence"}]

        mock_self = MagicMock()
        mock_self.FeatureCvterm_feature_Feature.all.return_value = mock_qs

        result = get_feature_cvterm(mock_self)
        self.assertIsNotNone(result)


class GetFeatureLocationTest(TestCase):
    """Tests for get_feature_location."""

    @override_settings(
        MACHADO_JBROWSE_URL="http://localhost/jbrowse",
        MACHADO_JBROWSE_OFFSET=500,
        MACHADO_JBROWSE_TRACKS="ref_seq,gene",
    )
    def test_location_with_jbrowse_full_settings(self):
        mock_loc = MagicMock()
        mock_loc.srcfeature.uniquename = "chr1"
        mock_loc.srcfeature.organism.genus = "Glycine"
        mock_loc.srcfeature.organism.species = "max"
        mock_loc.srcfeature.organism.infraspecific_name = None
        mock_loc.fmin = 1000
        mock_loc.fmax = 2000
        mock_loc.strand = 1

        mock_self = MagicMock()
        mock_self.Featureloc_feature_Feature.all.return_value = [mock_loc]

        result = get_feature_location(mock_self)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["start"], 1000)
        self.assertEqual(result[0]["end"], 2000)
        self.assertEqual(result[0]["strand"], 1)
        self.assertEqual(result[0]["ref"], "chr1")
        self.assertIn("jbrowse", result[0]["jbrowse_url"])
        self.assertIn("ref_seq,gene", result[0]["jbrowse_url"])

    @override_settings(
        MACHADO_JBROWSE_URL="http://localhost/jbrowse",
        MACHADO_JBROWSE_OFFSET=500,
        MACHADO_JBROWSE_TRACKS="ref_seq,gene",
    )
    def test_location_with_infraspecific_name(self):
        mock_loc = MagicMock()
        mock_loc.srcfeature.uniquename = "chr1"
        mock_loc.srcfeature.organism.genus = "Glycine"
        mock_loc.srcfeature.organism.species = "max"
        mock_loc.srcfeature.organism.infraspecific_name = "Wm82"
        mock_loc.fmin = 1000
        mock_loc.fmax = 2000
        mock_loc.strand = 1

        mock_self = MagicMock()
        mock_self.Featureloc_feature_Feature.all.return_value = [mock_loc]

        result = get_feature_location(mock_self)
        self.assertEqual(len(result), 1)
        self.assertIn("Wm82", result[0]["jbrowse_url"])

    @override_settings(MACHADO_JBROWSE_URL="http://localhost/jbrowse")
    def test_location_default_tracks_and_offset(self):
        """Test defaults when MACHADO_JBROWSE_TRACKS and MACHADO_JBROWSE_OFFSET are not set."""
        from django.conf import settings

        if hasattr(settings, "MACHADO_JBROWSE_TRACKS"):
            delattr(settings, "MACHADO_JBROWSE_TRACKS")
        if hasattr(settings, "MACHADO_JBROWSE_OFFSET"):
            delattr(settings, "MACHADO_JBROWSE_OFFSET")

        mock_loc = MagicMock()
        mock_loc.srcfeature.uniquename = "chr1"
        mock_loc.srcfeature.organism.genus = "Glycine"
        mock_loc.srcfeature.organism.species = "max"
        mock_loc.srcfeature.organism.infraspecific_name = None
        mock_loc.fmin = 1000
        mock_loc.fmax = 2000
        mock_loc.strand = 1

        mock_self = MagicMock()
        mock_self.Featureloc_feature_Feature.all.return_value = [mock_loc]

        result = get_feature_location(mock_self)
        self.assertEqual(len(result), 1)
        # Default tracks
        self.assertIn("ref_seq,gene,transcripts,CDS", result[0]["jbrowse_url"])
        # Default offset=1000: fmin-1000=0, fmax+1000=3000
        self.assertIn("0..3000", result[0]["jbrowse_url"])

    def test_location_no_jbrowse_url(self):
        """When MACHADO_JBROWSE_URL is not set, jbrowse_url should be None."""
        from django.conf import settings

        if hasattr(settings, "MACHADO_JBROWSE_URL"):
            delattr(settings, "MACHADO_JBROWSE_URL")

        mock_loc = MagicMock()
        mock_loc.srcfeature = None  # srcfeature is None

        mock_self = MagicMock()
        mock_self.Featureloc_feature_Feature.all.return_value = [mock_loc]

        result = get_feature_location(mock_self)
        self.assertEqual(result, [])

    def test_location_srcfeature_none(self):
        """When srcfeature is None, the location should be skipped."""
        mock_loc = MagicMock()
        mock_loc.srcfeature = None

        mock_self = MagicMock()
        mock_self.Featureloc_feature_Feature.all.return_value = [mock_loc]

        result = get_feature_location(mock_self)
        self.assertEqual(result, [])

    def test_location_empty(self):
        mock_self = MagicMock()
        mock_self.Featureloc_feature_Feature.all.return_value = []
        result = get_feature_location(mock_self)
        self.assertEqual(result, [])


class MachadoFeatureMethodsTest(TestCase):
    """Tests for the machado_feature_methods decorator."""

    def test_decorator_adds_methods(self):
        @machado_feature_methods()
        class DummyFeature:
            pass

        self.assertTrue(hasattr(DummyFeature, "get_dbxrefs"))
        self.assertTrue(hasattr(DummyFeature, "get_display"))
        self.assertTrue(hasattr(DummyFeature, "get_product"))
        self.assertTrue(hasattr(DummyFeature, "get_description"))
        self.assertTrue(hasattr(DummyFeature, "get_note"))
        self.assertTrue(hasattr(DummyFeature, "get_annotation"))
        self.assertTrue(hasattr(DummyFeature, "get_doi"))
        self.assertTrue(hasattr(DummyFeature, "get_orthologous_group"))
        self.assertTrue(hasattr(DummyFeature, "get_coexpression_group"))
        self.assertTrue(hasattr(DummyFeature, "get_expression_samples"))
        self.assertTrue(hasattr(DummyFeature, "get_relationship"))
        self.assertTrue(hasattr(DummyFeature, "get_cvterm"))
        self.assertTrue(hasattr(DummyFeature, "get_location"))
        self.assertTrue(hasattr(DummyFeature, "get_properties"))
        self.assertTrue(hasattr(DummyFeature, "get_synonyms"))


class GetPubAuthorsTest(TestCase):
    """Tests for get_pub_authors."""

    def test_authors(self):
        mock_qs = MagicMock()
        mock_qs.order_by.return_value.annotate.return_value.values_list.return_value = [
            "Smith John",
            "Doe Jane",
        ]

        mock_self = MagicMock()
        mock_self.Pubauthor_pub_Pub = mock_qs

        result = get_pub_authors(mock_self)
        self.assertEqual(result, "Smith John, Doe Jane")


class GetPubDoiTest(TestCase):
    """Tests for get_pub_doi."""

    def test_doi(self):
        mock_pub_dbxref = MagicMock()
        mock_pub_dbxref.dbxref.accession = "10.1234/test"

        mock_self = MagicMock()
        mock_self.PubDbxref_pub_Pub.filter.return_value.first.return_value = (
            mock_pub_dbxref
        )

        result = get_pub_doi(mock_self)
        self.assertEqual(result, "10.1234/test")


class MachadoPubMethodsTest(TestCase):
    """Tests for the machado_pub_methods decorator."""

    def test_decorator_adds_methods(self):
        @machado_pub_methods()
        class DummyPub:
            pass

        self.assertTrue(hasattr(DummyPub, "get_authors"))
        self.assertTrue(hasattr(DummyPub, "get_doi"))
