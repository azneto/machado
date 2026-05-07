# Copyright 2018 by Embrapa.  All rights reserved.
#
# This code is part of the machado distribution and governed by its
# license. Please see the LICENSE.txt and README.md files that should
# have been included as part of this package for licensing information.

"""Tests for sequence loader."""

from django.test import TestCase
from Bio.SeqRecord import SeqRecord
from Bio.Seq import Seq
from machado.loaders.sequence import SequenceLoader
from machado.loaders.exceptions import ImportingError
from machado.models import Organism, Db, Dbxref, Cv, Cvterm, Pub, PubDbxref, Feature, FeaturePub

class SequenceLoaderTest(TestCase):
    def setUp(self):
        self.org = Organism.objects.create(genus="Genus", species="species")
        self.db_rel = Cv.objects.create(name="relationship")
        self.db_seq = Cv.objects.create(name="sequence")
        self.db_internal = Db.objects.create(name="internal")
        self.dbxref_loc = Dbxref.objects.create(db=self.db_internal, accession="located_in")
        self.cvterm_loc = Cvterm.objects.get_or_create(
            name="located in", cv=self.db_rel, dbxref=self.dbxref_loc,
            is_obsolete=0, is_relationshiptype=1
        )[0]
        
        self.dbxref_gene = Dbxref.objects.create(db=self.db_internal, accession="gene")
        self.cvterm_gene = Cvterm.objects.get_or_create(
            name="gene", cv=self.db_seq, dbxref=self.dbxref_gene,
            is_obsolete=0, is_relationshiptype=0
        )[0]

    def test_init_without_doi(self):
        loader = SequenceLoader("test.fa", self.org)
        self.assertEqual(loader.filename, "test.fa")
        self.assertTrue(Db.objects.filter(name="FASTA_SOURCE").exists())

    def test_init_with_doi(self):
        db_doi = Db.objects.create(name="DOI")
        dbxref_doi = Dbxref.objects.create(db=db_doi, accession="10.1234/test")
        pub = Pub.objects.create(uniquename="test_pub", type_id=self.cvterm_gene.cvterm_id)
        PubDbxref.objects.create(pub=pub, dbxref=dbxref_doi, is_current=True)
        
        loader = SequenceLoader("test.fa", self.org, doi="10.1234/test")
        self.assertIsNotNone(loader.pub_dbxref_doi)

    def test_init_with_doi_fail_dbxref(self):
        with self.assertRaises(ImportingError):
            SequenceLoader("test.fa", self.org, doi="10.1234/nonexistent")

    def test_store_biopython_seq_record_success(self):
        loader = SequenceLoader("test.fa", self.org)
        seq_record = SeqRecord(Seq("ATGC"), id="feat1", description="Description 1")
        loader.store_biopython_seq_record(seq_record, "gene")
        
        feature = Feature.objects.get(uniquename="feat1")
        self.assertEqual(feature.residues, "ATGC")
        self.assertEqual(feature.name, "Description 1")
        self.assertEqual(feature.seqlen, 4)

    def test_store_biopython_seq_record_already_exists(self):
        loader = SequenceLoader("test.fa", self.org)
        seq_record = SeqRecord(Seq("ATGC"), id="feat1")
        loader.store_biopython_seq_record(seq_record, "gene")
        
        with self.assertRaisesRegex(ImportingError, "already registered"):
            loader.store_biopython_seq_record(seq_record, "gene")

    def test_store_biopython_seq_record_with_doi(self):
        db_doi = Db.objects.create(name="DOI")
        dbxref_doi = Dbxref.objects.create(db=db_doi, accession="10.1234/test")
        pub = Pub.objects.create(uniquename="test_pub", type_id=self.cvterm_gene.cvterm_id)
        PubDbxref.objects.create(pub=pub, dbxref=dbxref_doi, is_current=True)
        
        loader = SequenceLoader("test.fa", self.org, doi="10.1234/test")
        seq_record = SeqRecord(Seq("ATGC"), id="feat1")
        loader.store_biopython_seq_record(seq_record, "gene")
        
        feature = Feature.objects.get(uniquename="feat1")
        self.assertTrue(FeaturePub.objects.filter(feature=feature, pub=pub).exists())

    def test_add_sequence_to_feature_success(self):
        loader = SequenceLoader("test.fa", self.org)
        # Create feature first without residues
        Feature.objects.create(
            organism=self.org, uniquename="feat1", type=self.cvterm_gene,
            is_analysis=False, is_obsolete=False, timeaccessioned="2023-01-01T00:00:00Z", timelastmodified="2023-01-01T00:00:00Z"
        )
        
        seq_record = SeqRecord(Seq("ATGC"), id="feat1")
        loader.add_sequence_to_feature(seq_record, "gene")
        
        feature = Feature.objects.get(uniquename="feat1")
        self.assertEqual(feature.residues, "ATGC")

    def test_add_sequence_to_feature_fail(self):
        loader = SequenceLoader("test.fa", self.org)
        seq_record = SeqRecord(Seq("ATGC"), id="nonexistent")
        with self.assertRaisesRegex(ImportingError, "does NOT exist"):
            loader.add_sequence_to_feature(seq_record, "gene")

    def test_store_biopython_seq_record_ignore_residues(self):
        loader = SequenceLoader("test.fa", self.org)
        seq_record = SeqRecord(Seq("ATGC"), id="feat2")
        loader.store_biopython_seq_record(seq_record, "gene", ignore_residues=True)
        feature = Feature.objects.get(uniquename="feat2")
        self.assertEqual(feature.residues, "")
