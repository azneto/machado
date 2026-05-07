# Copyright 2018 by Embrapa.  All rights reserved.
#
# This code is part of the machado distribution and governed by its
# license. Please see the LICENSE.txt and README.md files that should
# have been included as part of this package for licensing information.

"""Tests for similarity loader."""

from django.test import TestCase
from unittest.mock import MagicMock
from machado.loaders.similarity import SimilarityLoader

from machado.models import (
    Cvterm,
    Cv,
    Dbxref,
    Db,
    Organism,
    Feature,
    FeatureRelationship,
    Featureloc,
)


class SimilarityLoaderTest(TestCase):
    def setUp(self):
        self.db_internal = Db.objects.create(name="internal")
        self.dbxref_loc = Dbxref.objects.create(
            db=self.db_internal, accession="located_in"
        )
        self.cv_rel = Cv.objects.create(name="relationship")
        self.cvterm_loc = Cvterm.objects.create(
            name="located in",
            cv=self.cv_rel,
            dbxref=self.dbxref_loc,
            is_obsolete=0,
            is_relationshiptype=1,
        )

        self.cv_seq = Cv.objects.create(name="sequence")
        self.dbxref_match = Dbxref.objects.create(
            db=self.db_internal, accession="match_part"
        )
        self.cvterm_match = Cvterm.objects.create(
            name="match_part",
            cv=self.cv_seq,
            dbxref=self.dbxref_match,
            is_obsolete=0,
            is_relationshiptype=0,
        )

        self.dbxref_sim = Dbxref.objects.create(
            db=self.db_internal, accession="similarity"
        )
        self.cvterm_sim = Cvterm.objects.create(
            name="in similarity relationship with",
            cv=self.cv_rel,
            dbxref=self.dbxref_sim,
            is_obsolete=0,
            is_relationshiptype=1,
        )

        self.org_q = Organism.objects.create(genus="GenusQ", species="speciesQ")
        self.org_s = Organism.objects.create(genus="GenusS", species="speciesS")

        self.dbxref_mrna = Dbxref.objects.create(db=self.db_internal, accession="mRNA")
        self.type_mrna = Cvterm.objects.create(
            name="mRNA",
            cv=self.cv_seq,
            dbxref=self.dbxref_mrna,
            is_obsolete=0,
            is_relationshiptype=0,
        )

    def test_init_success(self):
        loader = SimilarityLoader(
            filename="test.xml",
            program="blast",
            programversion="2.1",
            so_query="mRNA",
            so_subject="mRNA",
            org_query="GenusQ speciesQ",
            org_subject="GenusS speciesS",
            input_format="blast-xml",
        )
        self.assertIsNotNone(loader.analysis)

    def test_retrieve_id_from_description(self):
        loader = SimilarityLoader(
            filename="test.xml",
            program="blast",
            programversion="2.1",
            so_query="mRNA",
            so_subject="mRNA",
            org_query="GenusQ speciesQ",
            org_subject="GenusS speciesS",
            input_format="blast-xml",
        )
        self.assertEqual(
            loader.retrieve_id_from_description("some data id=FEAT1 more data"), "FEAT1"
        )
        self.assertIsNone(loader.retrieve_id_from_description("no id here"))

    def test_store_match_part(self):
        loader = SimilarityLoader(
            filename="test.xml",
            program="blast",
            programversion="2.1",
            so_query="mRNA",
            so_subject="mRNA",
            org_query="GenusQ speciesQ",
            org_subject="GenusS speciesS",
            input_format="blast-xml",
        )
        q_feat = Feature.objects.create(
            organism=self.org_q,
            uniquename="q1",
            type=self.type_mrna,
            is_analysis=False,
            is_obsolete=False,
            timeaccessioned="2023-01-01T00:00:00Z",
            timelastmodified="2023-01-01T00:00:00Z",
        )
        s_feat = Feature.objects.create(
            organism=self.org_s,
            uniquename="s1",
            type=self.type_mrna,
            is_analysis=False,
            is_obsolete=False,
            timeaccessioned="2023-01-01T00:00:00Z",
            timelastmodified="2023-01-01T00:00:00Z",
        )

        loader.store_match_part(
            query_feature_id=q_feat.feature_id,
            subject_feature_id=s_feat.feature_id,
            identity=90.0,
            query_start=0,
            query_end=100,
            subject_start=50,
            subject_end=150,
        )

        self.assertTrue(
            Featureloc.objects.filter(srcfeature_id=q_feat.feature_id).exists()
        )
        self.assertTrue(
            Featureloc.objects.filter(srcfeature_id=s_feat.feature_id).exists()
        )

    def test_store_feature_relationship(self):
        loader = SimilarityLoader(
            filename="test.xml",
            program="blast",
            programversion="2.1",
            so_query="mRNA",
            so_subject="mRNA",
            org_query="GenusQ speciesQ",
            org_subject="GenusS speciesS",
            input_format="blast-xml",
        )
        q_feat = Feature.objects.create(
            organism=self.org_q,
            uniquename="q2",
            type=self.type_mrna,
            is_analysis=False,
            is_obsolete=False,
            timeaccessioned="2023-01-01T00:00:00Z",
            timelastmodified="2023-01-01T00:00:00Z",
        )
        s_feat = Feature.objects.create(
            organism=self.org_s,
            uniquename="s2",
            type=self.type_mrna,
            is_analysis=False,
            is_obsolete=False,
            timeaccessioned="2023-01-01T00:00:00Z",
            timelastmodified="2023-01-01T00:00:00Z",
        )

        loader.store_feature_relationship(q_feat.feature_id, s_feat.feature_id)

        self.assertTrue(
            FeatureRelationship.objects.filter(
                object_id=q_feat.feature_id, subject_id=s_feat.feature_id
            ).exists()
        )

    def test_store_bio_searchio_query_result(self):
        loader = SimilarityLoader(
            filename="test.xml",
            program="blast",
            programversion="2.1",
            so_query="mRNA",
            so_subject="mRNA",
            org_query="GenusQ speciesQ",
            org_subject="GenusS speciesS",
            input_format="blast-xml",
        )

        Feature.objects.create(
            organism=self.org_q,
            uniquename="QID",
            type=self.type_mrna,
            is_analysis=False,
            is_obsolete=False,
            timeaccessioned="2023-01-01T00:00:00Z",
            timelastmodified="2023-01-01T00:00:00Z",
        )
        Feature.objects.create(
            organism=self.org_s,
            uniquename="SID",
            type=self.type_mrna,
            is_analysis=False,
            is_obsolete=False,
            timeaccessioned="2023-01-01T00:00:00Z",
            timelastmodified="2023-01-01T00:00:00Z",
        )

        # Mock HSP
        hsp_mock = MagicMock()
        hsp_mock.query_id = "QID"
        hsp_mock.hit_id = "SID"
        hsp_mock.query_start = 0
        hsp_mock.query_end = 100
        hsp_mock.hit_start = 0
        hsp_mock.hit_end = 100
        hsp_mock.ident_num = None
        hsp_mock.bitscore = None
        hsp_mock.bitscore_raw = None
        hsp_mock.evalue = None

        query_result_mock = MagicMock()
        query_result_mock.hsps = [hsp_mock]

        loader.store_bio_searchio_query_result(query_result_mock)

        # Verify match_part created
        self.assertTrue(
            Feature.objects.filter(uniquename__contains="match_part").exists()
        )

    def test_retrieve_query_from_hsp_description_fallback(self):
        loader = SimilarityLoader(
            filename="test.xml",
            program="blast",
            programversion="2.1",
            so_query="mRNA",
            so_subject="mRNA",
            org_query="GenusQ speciesQ",
            org_subject="GenusS speciesS",
            input_format="blast-xml",
        )
        q_feat = Feature.objects.create(
            organism=self.org_q,
            uniquename="FEAT_DESC",
            type=self.type_mrna,
            is_analysis=False,
            is_obsolete=False,
            timeaccessioned="2023-01-01T00:00:00Z",
            timelastmodified="2023-01-01T00:00:00Z",
        )
        hsp_mock = MagicMock()
        hsp_mock.query_id = "NONEXISTENT"
        hsp_mock.query_description = "data id=FEAT_DESC"

        self.assertEqual(loader.retrieve_query_from_hsp(hsp_mock), q_feat.feature_id)

    def test_interproscan_mRNA_annotation(self):
        loader = SimilarityLoader(
            filename="test.xml",
            program="blast",
            programversion="2.1",
            so_query="polypeptide",
            so_subject="mRNA",
            org_query="GenusQ speciesQ",
            org_subject="GenusS speciesS",
            input_format="interproscan-xml",
        )

        dbxref_poly = Dbxref.objects.create(db=self.db_internal, accession="poly")
        type_poly = Cvterm.objects.create(
            name="polypeptide",
            cv=self.cv_seq,
            dbxref=dbxref_poly,
            is_obsolete=0,
            is_relationshiptype=0,
        )

        q_feat = Feature.objects.create(
            organism=self.org_q,
            uniquename="QPOLY",
            type=type_poly,
            is_analysis=False,
            is_obsolete=False,
            timeaccessioned="2023-01-01T00:00:00Z",
            timelastmodified="2023-01-01T00:00:00Z",
        )
        q_mrna = Feature.objects.create(
            organism=self.org_q,
            uniquename="QMRNA",
            type=self.type_mrna,
            is_analysis=False,
            is_obsolete=False,
            timeaccessioned="2023-01-01T00:00:00Z",
            timelastmodified="2023-01-01T00:00:00Z",
        )
        s_feat = Feature.objects.create(
            organism=self.org_s,
            uniquename="SID",
            type=self.type_mrna,
            is_analysis=False,
            is_obsolete=False,
            timeaccessioned="2023-01-01T00:00:00Z",
            timelastmodified="2023-01-01T00:00:00Z",
        )

        # Translation of relationship
        dbxref_trans = Dbxref.objects.create(
            db=self.db_internal, accession="translation_of"
        )
        type_trans = Cvterm.objects.create(
            name="translation_of",
            cv=self.cv_seq,
            dbxref=dbxref_trans,
            is_obsolete=0,
            is_relationshiptype=1,
        )
        FeatureRelationship.objects.create(
            object=q_feat, subject=q_mrna, type=type_trans, rank=0
        )

        hsp_mock = MagicMock()
        hsp_mock.query_id = "QPOLY"
        hsp_mock.hit_id = "SID"
        hsp_mock.query_start = 0
        hsp_mock.query_end = 100
        hsp_mock.hit_start = 0
        hsp_mock.hit_end = 100
        hsp_mock.ident_num = None
        hsp_mock.bitscore = None
        hsp_mock.bitscore_raw = None
        hsp_mock.evalue = None

        query_result_mock = MagicMock()
        query_result_mock.hsps = [hsp_mock]

        loader.store_bio_searchio_query_result(query_result_mock)

        # Verify relationship with parent mRNA created
        self.assertTrue(
            FeatureRelationship.objects.filter(
                object_id=q_mrna.feature_id, subject_id=s_feat.feature_id
            ).exists()
        )
