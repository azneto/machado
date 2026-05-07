# Copyright 2018 by Embrapa.  All rights reserved.
#
# This code is part of the machado distribution and governed by its
# license. Please see the LICENSE.txt and README.md files that should
# have been included as part of this package for licensing information.

"""Tests for analysis loader."""

from django.test import TestCase
from machado.loaders.analysis import AnalysisLoader

from machado.models import (
    Analysis,
    Analysisfeature,
    Analysisprop,
    Cv,
    Cvterm,
    Db,
    Dbxref,
    Organism,
    Feature,
    Assay,
    Acquisition,
    Quantification,
)
from machado.models import Contact, Arraydesign, Protocol


class AnalysisLoaderTest(TestCase):
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
        self.loader = AnalysisLoader()

        # Dependencies for Assay
        self.contact = Contact.objects.create(name="test contact")
        self.db_seq = Cv.objects.create(name="sequence")
        self.dbxref_gene = Dbxref.objects.create(db=self.db_internal, accession="gene")
        self.type_gene = Cvterm.objects.create(
            name="gene",
            cv=self.db_seq,
            dbxref=self.dbxref_gene,
            is_obsolete=0,
            is_relationshiptype=0,
        )

        self.arraydesign = Arraydesign.objects.create(
            manufacturer=self.contact, platformtype=self.type_gene, name="test array"
        )
        self.protocol = Protocol.objects.create(
            type=self.type_gene, name="test protocol"
        )

        # mRNA type for Analysisfeature
        self.dbxref_mrna = Dbxref.objects.create(db=self.db_internal, accession="mRNA")
        self.type_mrna = Cvterm.objects.create(
            name="mRNA",
            cv=self.db_seq,
            dbxref=self.dbxref_mrna,
            is_obsolete=0,
            is_relationshiptype=0,
        )

    def create_assay(self, **kwargs):
        defaults = {
            "arraydesign": self.arraydesign,
            "protocol": self.protocol,
            "operator": self.contact,
        }
        defaults.update(kwargs)
        return Assay.objects.create(**defaults)

    def test_store_analysis_success(self):
        analysis = self.loader.store_analysis(
            program="blast",
            sourcename="test.xml",
            programversion="2.1",
            filename="test.xml",
            name="Test Blast",
            description="Blast description",
        )
        self.assertEqual(analysis.name, "Test Blast")
        self.assertTrue(
            Analysisprop.objects.filter(analysis=analysis, value="test.xml").exists()
        )

    def test_store_analysis_with_date(self):
        analysis = self.loader.store_analysis(
            program="blast",
            sourcename="test.xml",
            programversion="2.1",
            timeexecuted="Oct-16-2016",
        )
        self.assertEqual(analysis.timeexecuted.year, 2016)
        self.assertEqual(analysis.timeexecuted.month, 10)
        self.assertEqual(analysis.timeexecuted.day, 16)

    def test_store_quantification(self):
        db_sra = Db.objects.create(name="SRA")
        dbxref_sra = Dbxref.objects.create(db=db_sra, accession="SRR123")
        assay = self.create_assay(dbxref=dbxref_sra, name="Assay 1")
        analysis = Analysis.objects.create(
            program="p",
            sourcename="s",
            programversion="v",
            timeexecuted="2023-01-01T00:00:00Z",
        )

        self.loader.store_quantification(analysis, "SRR123")

        self.assertTrue(Acquisition.objects.filter(assay=assay, name="SRR123").exists())
        self.assertTrue(Quantification.objects.filter(analysis=analysis).exists())

    def test_store_quantification_by_name(self):
        assay = self.create_assay(name="AssayName")
        analysis = Analysis.objects.create(
            program="p",
            sourcename="s",
            programversion="v",
            timeexecuted="2023-01-01T00:00:00Z",
        )
        self.loader.store_quantification(analysis, "AssayName")
        self.assertEqual(Acquisition.objects.get(name="AssayName").assay, assay)

    def test_store_analysisfeature(self):
        org = Organism.objects.create(genus="G", species="s")
        feature = Feature.objects.create(
            organism=org,
            uniquename="feat1",
            type=self.type_mrna,
            is_analysis=False,
            is_obsolete=False,
            timeaccessioned="2023-01-01T00:00:00Z",
            timelastmodified="2023-01-01T00:00:00Z",
        )
        analysis = Analysis.objects.create(
            program="p",
            sourcename="s",
            programversion="v",
            timeexecuted="2023-01-01T00:00:00Z",
        )

        self.loader.store_analysisfeature(analysis, feature, org, rawscore=100.0)

        self.assertTrue(
            Analysisfeature.objects.filter(
                analysis=analysis, feature=feature, rawscore=100.0
            ).exists()
        )

    def test_store_analysisfeature_by_name(self):
        org = Organism.objects.create(genus="Genus", species="species")
        feature = Feature.objects.create(
            organism=org,
            uniquename="feat2",
            type=self.type_mrna,
            is_analysis=False,
            is_obsolete=False,
            timeaccessioned="2023-01-01T00:00:00Z",
            timelastmodified="2023-01-01T00:00:00Z",
        )
        analysis = Analysis.objects.create(
            program="p",
            sourcename="s",
            programversion="v",
            timeexecuted="2023-01-01T00:00:00Z",
        )

        self.loader.store_analysisfeature(
            analysis, "feat2", "Genus species", identity=95.0
        )
        self.assertEqual(
            Analysisfeature.objects.get(analysis=analysis, identity=95.0).feature,
            feature,
        )
