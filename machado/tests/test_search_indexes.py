# Copyright 2018 by Embrapa.  All rights reserved.
#
# This code is part of the machado distribution and governed by its
# license. Please see the LICENSE.txt and README.md files that should
# have been included as part of this package for licensing information.

"""Tests for search indexes."""

from unittest.mock import MagicMock, patch
from django.test import TestCase, override_settings
from django.core.exceptions import ObjectDoesNotExist
from machado.models import (
    Organism,
    Feature,
    Cvterm,
    Cv,
    Dbxref,
    Db,
)
from machado.search_indexes import FeatureIndex


class FeatureIndexTest(TestCase):
    """Test suite for FeatureIndex."""

    def setUp(self):
        """Set up test context."""
        # Setup basic data for tests
        self.db = Db.objects.create(name="test_db")
        self.dbxref = Dbxref.objects.create(
            db=self.db, accession="test_acc", version="1"
        )
        self.cv_seq = Cv.objects.create(name="sequence")
        self.cv_prop = Cv.objects.create(name="feature_property")
        self.type_gene = Cvterm.objects.create(
            name="gene",
            cv=self.cv_seq,
            dbxref=self.dbxref,
            is_obsolete=0,
            is_relationshiptype=0,
        )
        self.org = Organism.objects.create(
            genus="Genus", species="species", common_name="Common"
        )
        self.index = FeatureIndex()
        self.feature = Feature.objects.create(
            organism=self.org,
            uniquename="test_feature",
            name="Test Feature",
            type=self.type_gene,
            is_analysis=False,
            is_obsolete=False,
            timeaccessioned="2023-01-01T00:00:00Z",
            timelastmodified="2023-01-01T00:00:00Z",
        )

    def test_get_model(self):
        """Test get model."""
        self.assertEqual(self.index.get_model(), Feature)

    @override_settings(MACHADO_VALID_TYPES=["gene"])
    def test_index_queryset(self):
        """Test index queryset."""
        qs = self.index.index_queryset()
        self.assertIn(self.feature, qs)

    def test_index_queryset_error(self):
        """Test index queryset error."""
        with patch("machado.search_indexes.FeatureIndex.get_model") as mock_model:
            mock_model.side_effect = AttributeError
            with self.assertRaises(AttributeError):
                self.index.index_queryset()

    def test_prepare_organism(self):
        """Test prepare organism."""
        self.assertEqual(self.index.prepare_organism(self.feature), "Genus species")
        self.feature.organism.infraspecific_name = "infra"
        self.assertEqual(
            self.index.prepare_organism(self.feature), "Genus species infra"
        )

    @patch("machado.search_indexes.VALID_PROGRAMS", [("blast",)])
    @patch("machado.search_indexes.Featureloc.objects.filter")
    @patch("machado.search_indexes.Analysisfeature.objects.filter")
    def test_prepare_analyses(self, mock_af_filter, mock_fl_filter):
        """Test prepare analyses."""
        mock_fl_filter.return_value.filter.return_value.filter.return_value.filter.return_value.values_list.return_value = [
            1
        ]
        mock_af_filter.return_value.values_list.return_value.distinct.return_value = [
            ("blast",)
        ]

        result = self.index.prepare_analyses(self.feature)
        self.assertEqual(result, ["blast matches"])

        mock_af_filter.return_value.values_list.return_value.distinct.return_value = []
        result = self.index.prepare_analyses(self.feature)
        self.assertEqual(result, ["no blast matches"])

    @patch("machado.search_indexes.FeatureDbxref.objects.filter")
    @patch("machado.search_indexes.FeatureCvterm.objects.filter")
    @patch("machado.search_indexes.FeatureRelationship.objects.filter")
    def test_prepare_text(self, mock_fr_filter, mock_fc_filter, mock_fd_filter):
        """Test prepare text."""
        feature = MagicMock()
        feature.uniquename = "test_feat"
        feature.name = "Test Feat"
        # Mock methods injected by decorator
        feature.get_display.return_value = "Display Name"
        feature.get_annotation.return_value = ["Annotation"]
        feature.get_doi.return_value = ["10.1234/test"]
        feature.get_expression_samples.return_value = []

        # Mock DBxRef
        mock_dbxref = MagicMock()
        mock_dbxref.dbxref.accession = "ACC123"
        mock_fd_filter.return_value = [mock_dbxref]

        # Mock CVTerm
        mock_fc = MagicMock()
        mock_fc.cvterm.dbxref.db.name = "GO"
        mock_fc.cvterm.dbxref.accession = "000123"
        mock_fc.cvterm.name = "biological_process"
        mock_fc_filter.return_value = [mock_fc]

        # Mock relationships
        mock_fr_filter.return_value = []

        text = self.index.prepare_text(feature)
        self.assertIn("Display Name", text)
        self.assertIn("ACC123", text)
        self.assertIn("GO:000123", text)
        self.assertIn("biological_process", text)
        self.assertIn("Annotation", text)
        self.assertIn("10.1234/test", text)

        # Test protein match
        mock_fr = MagicMock()
        mock_fr.subject.uniquename = "PROT1"
        mock_fr.subject.name = "Protein 1"
        mock_fr_filter.return_value = [mock_fr]
        text = self.index.prepare_text(feature)
        self.assertIn("PROT1", text)
        self.assertIn("Protein 1", text)

        # Test expression samples
        feature.get_expression_samples.return_value = [
            {
                "assay_name": "assay1",
                "biomaterial_name": "bio1",
                "biomaterial_description": "bio desc",
                "treatment_name": "treat name",
            }
        ]
        text = self.index.prepare_text(feature)
        self.assertIn("assay1", text)
        self.assertIn("bio1", text)
        self.assertIn("desc", text)
        self.assertIn("treat", text)

        # Test overlapping features
        self.index.has_overlapping_features = True
        with patch(
            "machado.search_indexes.Featureloc.objects.filter"
        ) as mock_fl_filter:
            mock_loc = MagicMock()
            mock_loc.feature.uniquename = "OVERLAP1"
            mock_loc.feature.name = "Overlap 1"
            mock_fl_filter.return_value = [mock_loc]
            # Mock the reverse relation
            loc_inst = MagicMock()
            loc_inst.fmin = 100
            loc_inst.fmax = 200
            loc_inst.srcfeature = 1
            loc_inst.feature.type.name = "gene"
            feature.Featureloc_feature_Feature.filter.return_value = [loc_inst]
            text = self.index.prepare_text(feature)
            self.assertIn("OVERLAP1", text)
            self.assertIn("Overlap 1", text)

        # Test no name
        feature.name = None
        text = self.index.prepare_text(feature)
        self.assertNotIn("None", text)

        # Test no display
        feature.get_display.return_value = None
        text = self.index.prepare_text(feature)

        # Test overlapping features AttributeError
        self.index.has_overlapping_features = True
        feature_no_rel = MagicMock(
            spec=[
                "get_display",
                "get_annotation",
                "get_doi",
                "get_expression_samples",
                "uniquename",
                "name",
            ]
        )
        feature_no_rel.get_display.return_value = "Display"
        feature_no_rel.get_annotation.return_value = []
        feature_no_rel.get_doi.return_value = []
        feature_no_rel.get_expression_samples.return_value = []
        with self.assertRaises(AttributeError):
            self.index.prepare_text(feature_no_rel)

    def test_prepare_doi(self):
        """Test prepare doi."""
        self.feature.get_doi = MagicMock(return_value=["doi1"])
        self.assertEqual(self.index.prepare_doi(self.feature), ["doi1"])

    def test_prepare_orthology(self):
        """Test prepare orthology."""
        self.feature.get_orthologous_group = MagicMock(return_value="OG1")
        self.assertTrue(self.index.prepare_orthology(self.feature))
        self.assertEqual(self.index.prepare_orthologous_group(self.feature), "OG1")

    def test_prepare_coexpression(self):
        """Test prepare coexpression."""
        self.feature.get_coexpression_group = MagicMock(return_value="CG1")
        self.assertTrue(self.index.prepare_coexpression(self.feature))
        self.assertEqual(self.index.prepare_coexpression_group(self.feature), "CG1")

    def test_prepare_biomaterial_and_treatment(self):
        """Test prepare biomaterial and treatment."""
        sample = {"biomaterial_description": "desc", "treatment_name": "treat"}
        self.feature.get_expression_samples = MagicMock(return_value=[sample, sample])
        self.assertEqual(self.index.prepare_biomaterial(self.feature), ["desc"])
        self.assertEqual(self.index.prepare_treatment(self.feature), ["treat"])

    @patch("machado.search_indexes.Featureprop.objects.get")
    @patch("machado.search_indexes.Featureprop.objects.filter")
    @patch("machado.search_indexes.FeatureRelationship.objects.filter")
    def test_prepare_orthologs_biomaterial(
        self, mock_fr_filter, mock_fp_filter, mock_fp_get
    ):
        """Test prepare orthologs biomaterial."""
        mock_fp_get.return_value.value = "OG1"
        mock_fp_filter.return_value.values_list.return_value = [1, 2]

        mock_rel = MagicMock()
        mock_rel.subject.get_expression_samples.return_value = [
            {"biomaterial_description": "bio1"}
        ]
        mock_fr_filter.return_value = [mock_rel]

        result = self.index.prepare_orthologs_biomaterial(self.feature)
        self.assertEqual(result, ["bio1"])

        # Test ObjectDoesNotExist
        mock_fp_get.side_effect = ObjectDoesNotExist
        self.assertEqual(self.index.prepare_orthologs_biomaterial(self.feature), [])

    @patch("machado.search_indexes.Featureprop.objects.get")
    @patch("machado.search_indexes.Featureprop.objects.filter")
    @patch("machado.search_indexes.FeatureRelationship.objects.filter")
    def test_prepare_orthologs_coexpression(
        self, mock_fr_filter, mock_fp_filter, mock_fp_get
    ):
        """Test prepare orthologs coexpression."""
        mock_fp_get.return_value.value = "OG1"
        mock_fp_filter.return_value.values_list.return_value = [1, 2]

        mock_rel = MagicMock()
        mock_fr_filter.return_value = [mock_rel]

        # have_coexp = True
        with patch(
            "machado.search_indexes.Featureprop.objects.filter"
        ) as mock_fp_filter_inner:
            mock_fp_filter_inner.return_value.exists.return_value = True
            self.assertTrue(self.index.prepare_orthologs_coexpression(self.feature))

            # have_coexp = False
            mock_fp_filter_inner.return_value.exists.return_value = False
            self.assertFalse(self.index.prepare_orthologs_coexpression(self.feature))

        # Test ObjectDoesNotExist
        mock_fp_get.side_effect = ObjectDoesNotExist
        self.assertFalse(self.index.prepare_orthologs_coexpression(self.feature))

    def test_prepare_display(self):
        """Test prepare display."""
        self.feature.get_display = MagicMock(return_value="Display")
        self.assertEqual(self.index.prepare_display(self.feature), "Display")

    def test_prepare_relationship(self):
        """Test prepare relationship."""
        mock_r = MagicMock()
        mock_r.feature_id = 123
        mock_r.type.name = "part_of"
        self.feature.get_relationship = MagicMock(return_value=[mock_r])
        self.assertEqual(self.index.prepare_relationship(self.feature), ["123 part_of"])

    def test_prepare_autocomplete(self):
        """Test prepare autocomplete."""
        self.index.temp = "extra keywords"
        self.assertIn(
            "Genus species extra keywords",
            self.index.prepare_autocomplete(self.feature),
        )
        # Test infraspecific name
        self.feature.organism.infraspecific_name = "infra"
        self.assertIn(
            "Genus species infra extra keywords",
            self.index.prepare_autocomplete(self.feature),
        )
