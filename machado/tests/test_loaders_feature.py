# Copyright 2018 by Embrapa.  All rights reserved.
#
# This code is part of the machado distribution and governed by its
# license. Please see the LICENSE.txt and README.md files that should
# have been included as part of this package for licensing information.

"""Tests for feature loader."""

from datetime import datetime, timezone
from django.test import TestCase
from django.db.utils import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from unittest.mock import MagicMock, patch, PropertyMock
from machado.loaders.feature import (
    FeatureLoaderBase,
    FeatureLoader,
    MultispeciesFeatureLoader,
)
from machado.loaders.exceptions import ImportingError
from machado.models import (
    Cv,
    Cvterm,
    Db,
    Dbxref,
    Organism,
    Feature,
    Pub,
    PubDbxref,
    Featureloc,
    FeatureRelationship,
    FeatureDbxref,
    Featureprop,
    FeatureCvterm,
)


class FeatureLoaderTest(TestCase):
    """Test suite for FeatureLoader."""

    def setUp(self):
        """Set up test context."""
        self.db_internal = Db.objects.get_or_create(name="internal")[0]
        self.cv_rel = Cv.objects.get_or_create(name="relationship")[0]
        self.cv_seq = Cv.objects.get_or_create(name="sequence")[0]

        self.cvterm_loc = self.ensure_cvterm("located in", self.cv_rel)
        self.cvterm_poly = self.ensure_cvterm("polypeptide", self.cv_seq)
        self.cvterm_prot = self.ensure_cvterm("protein_match", self.cv_seq)

        self.org = Organism.objects.create(genus="Genus", species="species")

    def ensure_cvterm(self, name, cv):
        """ensure_cvterm."""
        dbxref, created = Dbxref.objects.get_or_create(
            db=self.db_internal, accession=f"acc_{name}"
        )
        return Cvterm.objects.get_or_create(
            name=name,
            cv=cv,
            is_obsolete=0,
            defaults={
                "dbxref": dbxref,
                "is_relationshiptype": 1 if cv.name == "relationship" else 0,
                "definition": "",
            },
        )[0]

    def create_feat(self, uniquename, type_obj, dbxref=None, organism=None):
        """create_feat."""
        if organism is None:
            organism = self.org
        if dbxref is None:
            dbxref = Dbxref.objects.create(
                db=self.db_internal, accession=f"dbx_{uniquename}"
            )
        return Feature.objects.create(
            organism=organism,
            uniquename=uniquename,
            type=type_obj,
            dbxref=dbxref,
            is_analysis=False,
            is_obsolete=False,
            timeaccessioned=datetime.now(timezone.utc),
            timelastmodified=datetime.now(timezone.utc),
        )

    def test_loader_base_init(self):
        """Test loader base init."""
        loader = FeatureLoaderBase("GFF", "test.gff")
        self.assertEqual(loader.filename, "test.gff")
        self.assertTrue(Db.objects.filter(name="GFF").exists())

    @patch("machado.models.Db.objects.get_or_create")
    def test_loader_base_init_integrity_error(self, mock_get_or_create):
        """Test loader base init integrity error."""
        mock_get_or_create.side_effect = IntegrityError("Mock Error")
        with self.assertRaises(ImportingError):
            FeatureLoaderBase("GFF_FAIL", "test.gff")

    def test_loader_base_init_with_doi(self):
        """Test loader base init with doi."""
        FeatureLoaderBase("GFF_INIT", "init.gff")
        db_doi = Db.objects.get_or_create(name="DOI")[0]
        dbxref_doi = Dbxref.objects.get_or_create(
            db=db_doi, accession="10.1234/test_doi"
        )[0]
        null_cvterm = Cvterm.objects.get(name="null", cv__name="null")
        pub = Pub.objects.create(
            uniquename="test_pub_doi", type=null_cvterm, is_obsolete=False
        )
        pub_dbxref = PubDbxref.objects.create(
            pub=pub, dbxref=dbxref_doi, is_current=True
        )
        loader = FeatureLoaderBase("GFF_DOI", "test.gff", doi="10.1234/test_doi")
        loader.pub_dbxref_doi = pub_dbxref
        self.assertIsNotNone(loader.pub_dbxref_doi)

    def test_loader_base_init_doi_fail(self):
        """Test loader base init doi fail."""
        with self.assertRaisesRegex(ImportingError, "not registered"):
            FeatureLoaderBase("GFF_DOI_FAIL", "test.gff", doi="nonexistent_doi")

    def test_loader_base_init_pub_dbxref_fail(self):
        """Test loader base init pub dbxref fail."""
        db_doi = Db.objects.get_or_create(name="DOI")[0]
        Dbxref.objects.get_or_create(db=db_doi, accession="10.1234/missing_pub")
        with self.assertRaisesRegex(
            ImportingError, "10.1234/missing_pub not registered"
        ):
            FeatureLoaderBase("GFF_P_FAIL", "test.gff", doi="10.1234/missing_pub")

    def test_feature_loader_init_fail(self):
        """Test feature loader init fail."""
        with self.assertRaisesRegex(ImportingError, "requires an organism parameter"):
            FeatureLoader("GFF_INIT_FAIL", "test.gff", None)

    @patch("machado.loaders.feature.FeatureAttributesLoader")
    def test_store_tabix_GFF_feature_success(self, MockAttrLoader):
        """Test store tabix GFF feature success."""
        loader = FeatureLoader("GFF_S", "test.gff", self.org)
        self.ensure_cvterm("mRNA", self.cv_seq)
        self.ensure_cvterm("translation_of", self.cv_seq)
        tabix_feat = MagicMock()
        tabix_feat.feature = "mRNA"
        tabix_feat.attributes = "ID=FEAT_S;Name=Name1"
        tabix_feat.contig = "CONTIG_S"
        tabix_feat.strand = "+"
        tabix_feat.frame = "."
        tabix_feat.start = 100
        tabix_feat.end = 200
        mock_attrs = MockAttrLoader.return_value
        mock_attrs.get_attributes.return_value = {
            "id": "FEAT_S",
            "name": "Name1",
        }
        db_fasta = Db.objects.get_or_create(name="FASTA_SOURCE")[0]
        dbxref_contig = Dbxref.objects.create(db=db_fasta, accession="CONTIG_S")
        self.create_feat(
            "CONTIG_S",
            self.ensure_cvterm("chromosome", self.cv_seq),
            dbxref=dbxref_contig,
        )
        loader.store_tabix_GFF_feature(tabix_feat, qtl=False)
        self.assertTrue(
            Feature.objects.filter(uniquename="FEAT_S", type__name="mRNA").exists()
        )
        self.assertTrue(
            Feature.objects.filter(
                uniquename="FEAT_S", type__name="polypeptide"
            ).exists()
        )

    @patch("machado.loaders.feature.FeatureAttributesLoader")
    def test_store_tabix_GFF_feature_so_term_fail(self, MockAttrLoader):
        """Test store tabix GFF feature so term fail."""
        loader = FeatureLoader("GFF_SO_F", "test.gff", self.org)
        tabix_feat = MagicMock()
        tabix_feat.feature = "nonexistent_so"
        tabix_feat.attributes = "ID=F_SO_F"
        mock_attrs = MockAttrLoader.return_value
        mock_attrs.get_attributes.return_value = {"id": "F_SO_F"}
        with self.assertRaisesRegex(ImportingError, "is not a sequence ontology term"):
            loader.store_tabix_GFF_feature(tabix_feat, qtl=False)

    @patch("machado.loaders.feature.FeatureAttributesLoader")
    def test_store_tabix_GFF_feature_contig_fail(self, MockAttrLoader):
        """Test store tabix GFF feature contig fail."""
        loader = FeatureLoader("GFF_C_F", "test.gff", self.org)
        self.ensure_cvterm("mRNA", self.cv_seq)
        tabix_feat = MagicMock()
        tabix_feat.feature = "mRNA"
        tabix_feat.attributes = "ID=F_C_F"
        tabix_feat.contig = "MISSING_CONTIG"
        mock_attrs = MockAttrLoader.return_value
        mock_attrs.get_attributes.return_value = {"id": "F_C_F"}
        Db.objects.get_or_create(name="FASTA_SOURCE")
        with self.assertRaisesRegex(ImportingError, "FASTA_SOURCE MISSING_CONTIG"):
            loader.store_tabix_GFF_feature(tabix_feat, qtl=False)

    @patch("machado.loaders.feature.FeatureAttributesLoader")
    def test_store_tabix_GFF_feature_strand_minus_and_phase_error(self, MockAttrLoader):
        """Test store tabix GFF feature strand minus and phase error."""
        loader = FeatureLoader("GFF_SM", "test.gff", self.org)
        self.ensure_cvterm("mRNA", self.cv_seq)
        tabix_feat = MagicMock()
        tabix_feat.feature = "mRNA"
        tabix_feat.attributes = "ID=F_SM"
        tabix_feat.contig = "C_SM"
        tabix_feat.strand = "-"
        # Use a property mock to trigger ValueError on phase access
        type(tabix_feat).frame = PropertyMock(side_effect=ValueError)
        tabix_feat.start = 100
        tabix_feat.end = 200
        mock_attrs = MockAttrLoader.return_value
        mock_attrs.get_attributes.return_value = {"id": "F_SM"}
        db_fasta = Db.objects.get_or_create(name="FASTA_SOURCE")[0]
        dbxref_c = Dbxref.objects.get_or_create(db=db_fasta, accession="C_SM")[0]
        self.create_feat(
            "C_SM",
            self.ensure_cvterm("chromosome", self.cv_seq),
            dbxref=dbxref_c,
        )
        self.ensure_cvterm("translation_of", self.cv_seq)
        loader.store_tabix_GFF_feature(tabix_feat, qtl=False)
        floc = Featureloc.objects.get(feature__uniquename="F_SM")
        self.assertEqual(floc.strand, -1)
        self.assertIsNone(floc.phase)

    @patch("machado.loaders.feature.FeatureAttributesLoader")
    def test_store_tabix_GFF_feature_no_id(self, MockAttrLoader):
        """Test store tabix GFF feature no id."""
        loader = FeatureLoader("GFF_NOID", "test.gff", self.org)
        self.ensure_cvterm("mRNA", self.cv_seq)
        self.ensure_cvterm("translation_of", self.cv_seq)
        tabix_feat = MagicMock()
        tabix_feat.feature = "mRNA"
        tabix_feat.attributes = "Name=Name_NOID"
        tabix_feat.contig = "CONTIG_NOID"
        tabix_feat.strand = "+"
        tabix_feat.frame = "."
        tabix_feat.start = 100
        tabix_feat.end = 200
        mock_attrs = MockAttrLoader.return_value
        mock_attrs.get_attributes.return_value = {"name": "Name_NOID"}
        db_fasta = Db.objects.get_or_create(name="FASTA_SOURCE")[0]
        dbxref_contig = Dbxref.objects.get_or_create(
            db=db_fasta, accession="CONTIG_NOID"
        )[0]
        self.create_feat(
            "CONTIG_NOID",
            self.ensure_cvterm("chromosome", self.cv_seq),
            dbxref=dbxref_contig,
        )
        loader.store_tabix_GFF_feature(tabix_feat, qtl=False)
        self.assertTrue(Feature.objects.filter(uniquename__startswith="auto").exists())

    @patch("machado.loaders.feature.FeatureAttributesLoader")
    def test_store_tabix_GFF_feature_qtl(self, MockAttrLoader):
        """Test store tabix GFF feature qtl."""
        loader = FeatureLoader("GFF_QTL", "test.gff", self.org)
        self.ensure_cvterm("QTL", self.cv_seq)
        tabix_feat = MagicMock()
        tabix_feat.feature = "trait"
        tabix_feat.attributes = "ID=QTL_F"
        tabix_feat.contig = "CONTIG_QTL"
        tabix_feat.strand = "."
        tabix_feat.frame = "."
        tabix_feat.start = 100
        tabix_feat.end = 200
        mock_attrs = MockAttrLoader.return_value
        mock_attrs.get_attributes.return_value = {"id": "QTL_F"}
        db_fasta = Db.objects.get_or_create(name="FASTA_SOURCE")[0]
        dbxref_contig = Dbxref.objects.get_or_create(
            db=db_fasta, accession="CONTIG_QTL"
        )[0]
        self.create_feat(
            "CONTIG_QTL",
            self.ensure_cvterm("chromosome", self.cv_seq),
            dbxref=dbxref_contig,
        )
        loader.store_tabix_GFF_feature(tabix_feat, qtl=True)
        self.assertTrue(
            Feature.objects.filter(uniquename="QTL_F", type__name="QTL").exists()
        )

    @patch("machado.loaders.feature.FeatureAttributesLoader")
    def test_store_tabix_GFF_feature_integrity_error(self, MockAttrLoader):
        """Test store tabix GFF feature integrity error."""
        loader = FeatureLoader("GFF_IE", "test.gff", self.org)
        self.ensure_cvterm("mRNA", self.cv_seq)
        tabix_feat = MagicMock()
        tabix_feat.feature = "mRNA"
        tabix_feat.attributes = "ID=FEAT_IE"
        mock_attrs = MockAttrLoader.return_value
        mock_attrs.get_attributes.return_value = {"id": "FEAT_IE"}
        # Create it once
        self.create_feat("FEAT_IE", self.ensure_cvterm("mRNA", self.cv_seq))
        # Now storing it again should trigger IntegrityError and then
        # ImportingError
        with self.assertRaises(ImportingError):
            loader.store_tabix_GFF_feature(tabix_feat, qtl=False)

    def test_store_relationship(self):
        """Test store relationship."""
        loader = FeatureLoader("GFF_REL", "test.gff", self.org)
        self.ensure_cvterm("part_of", self.cv_seq)
        gene_type = self.ensure_cvterm("gene", self.cv_seq)
        f1 = self.create_feat("f_rel_1", gene_type)
        f2 = self.create_feat("f_rel_2", gene_type)
        loader.store_relationship("f_rel_1", "f_rel_2")
        self.assertTrue(
            FeatureRelationship.objects.filter(subject=f1, object=f2).exists()
        )

    @patch("builtins.print")
    def test_store_relationship_not_found(self, mock_print):
        """Test store relationship not found."""
        loader = FeatureLoader("GFF_REL_NF", "test.gff", self.org)
        self.ensure_cvterm("part_of", self.cv_seq)
        loader.store_relationship("nonexistent_rel1", "nonexistent_rel2")

    def test_store_feature_dbxref(self):
        """Test store feature dbxref."""
        loader = FeatureLoader("GFF_DBX", "test.gff", self.org)
        f1 = self.create_feat("f_dbx_1", self.cvterm_poly)
        loader.store_feature_dbxref("f_dbx_1", "polypeptide", "EXT:ACC_DBX")
        self.assertTrue(
            FeatureDbxref.objects.filter(
                feature=f1, dbxref__accession="ACC_DBX", dbxref__db__name="EXT"
            ).exists()
        )

    def test_store_feature_groups(self):
        """Test store feature groups."""
        loader = FeatureLoader("GFF_GRP", "test.gff", self.org)
        mRNA_type = self.ensure_cvterm("mRNA_G", self.cv_seq)
        f1 = self.create_feat("f_grp_1", mRNA_type)
        f2 = self.create_feat("f_grp_2", mRNA_type)
        loader.store_feature_groups(
            ["f_grp_1", "f_grp_2"], mRNA_type, self.org, soterm="mRNA_G"
        )
        self.assertEqual(
            Featureprop.objects.filter(feature=f1, type=mRNA_type).count(), 1
        )
        self.assertEqual(
            Featureprop.objects.filter(feature=f2, type=mRNA_type).count(), 1
        )

    def test_store_feature_groups_acc_none(self):
        """Test store feature groups acc none."""
        loader = FeatureLoader("GFF_GRP_N", "test.gff", self.org)
        unique_type = self.ensure_cvterm("mRNA_U_N", self.cv_seq)
        loader.store_feature_groups(
            ["nonexistent_acc", None], unique_type, self.org, soterm="mRNA_U_N"
        )

    def test_store_feature_groups_integrity_error(self):
        """Test store feature groups integrity error."""
        loader = FeatureLoader("GFF_GRP_IE", "test.gff", self.org)
        mRNA_type = self.ensure_cvterm("mRNA_G_IE", self.cv_seq)
        f1 = self.create_feat("f_grp_ie_1", mRNA_type)
        self.create_feat("f_grp_ie_2", mRNA_type)
        # Create a prop manually to trigger IntegrityError on bulk_create
        Featureprop.objects.create(feature=f1, type=mRNA_type, value="val", rank=0)
        with self.assertRaises(ImportingError):
            loader.store_feature_groups(
                ["f_grp_ie_1", "f_grp_ie_2"],
                mRNA_type,
                self.org,
                soterm="mRNA_G_IE",
            )

    def test_multispecies_retrieve_feature_id(self):
        """Test multispecies retrieve feature id."""
        loader = MultispeciesFeatureLoader("SOURCE_M", "test.fa")
        f1 = self.create_feat("UNIQUE_M_1", self.cvterm_prot)
        self.assertEqual(
            loader.retrieve_feature_id("UNIQUE_M_1", "protein_match"),
            f1.feature_id,
        )

    def test_multispecies_retrieve_feature_id_fallbacks(self):
        """Test multispecies retrieve feature id fallbacks."""
        loader = MultispeciesFeatureLoader("SOURCE_F", "test.fa")
        mRNA_type = self.ensure_cvterm("mRNA_F", self.cv_seq)
        f2 = self.create_feat("mRNA_F-FEAT_F_2", mRNA_type)
        self.assertEqual(
            loader.retrieve_feature_id("FEAT_F_2", "mRNA_F"), f2.feature_id
        )
        f3 = self.create_feat("FEAT_F_3", mRNA_type)
        f3.name = "DISPLAY_F_3"
        f3.save()
        self.assertEqual(
            loader.retrieve_feature_id("DISPLAY_F_3", "mRNA_F"), f3.feature_id
        )
        db_f = Db.objects.get_or_create(name="FALLBACK")[0]
        dbxref4 = Dbxref.objects.create(db=db_f, accession="DBACC_F_4")
        f4 = self.create_feat("FEAT_F_4", mRNA_type, dbxref=dbxref4)
        self.assertEqual(
            loader.retrieve_feature_id("DBACC_F_4", "mRNA_F"), f4.feature_id
        )
        dbxref5 = Dbxref.objects.create(db=db_f, accession="SECACC_F_5")
        f5 = self.create_feat("FEAT_F_5", mRNA_type)
        FeatureDbxref.objects.create(feature=f5, dbxref=dbxref5, is_current=True)
        self.assertEqual(
            loader.retrieve_feature_id("SECACC_F_5", "mRNA_F"), f5.feature_id
        )

    def test_multispecies_retrieve_feature_id_fail(self):
        """Test multispecies retrieve feature id fail."""
        loader = MultispeciesFeatureLoader("SOURCE_FAIL", "test.fa")
        with self.assertRaises(ObjectDoesNotExist):
            loader.retrieve_feature_id("nonexistent_multi", "mRNA")

    def test_multispecies_store_bio_searchio_hit(self):
        """Test multispecies store bio searchio hit."""
        loader = MultispeciesFeatureLoader("SOURCE_HIT", "test.fa")
        hit_mock = MagicMock()
        hit_mock.id = "HIT_M_1"
        hit_mock.accession = "ACC_M_1"
        hit_mock.dbxrefs = ["GO:0001", "REF_HIT:X1"]
        db_go = Db.objects.get_or_create(name="GO")[0]
        dbxref_go = Dbxref.objects.get_or_create(db=db_go, accession="0001")[0]
        Cvterm.objects.get_or_create(
            name="term1",
            cv=self.cv_seq,
            dbxref=dbxref_go,
            is_obsolete=0,
            is_relationshiptype=0,
        )
        loader.store_bio_searchio_hit(hit_mock, target="Blast")
        self.assertTrue(Feature.objects.filter(uniquename="HIT_M_1").exists())
        feat = Feature.objects.get(uniquename="HIT_M_1")
        self.assertTrue(FeatureCvterm.objects.filter(feature=feat).exists())
        self.assertTrue(
            FeatureDbxref.objects.filter(feature=feat, dbxref__accession="X1").exists()
        )

    def test_multispecies_store_bio_searchio_hit_interpro(self):
        """Test multispecies store bio searchio hit interpro."""
        loader = MultispeciesFeatureLoader("SOURCE_IPR", "test.fa")
        hit_mock = MagicMock()
        hit_mock.id = "IPR_M_1"
        hit_mock.accession = "ACC_IPR_M"
        hit_mock.attributes = {"Target": "SIGNALP_V4"}
        hit_mock.dbxrefs = []
        loader.store_bio_searchio_hit(hit_mock, target="InterPro")
        self.assertTrue(Db.objects.filter(name="SIGNALP").exists())

    def test_multispecies_store_bio_searchio_hit_not_found(self):
        """Test multispecies store bio searchio hit not found."""
        loader = MultispeciesFeatureLoader("SOURCE_HIT_NF", "test.fa")
        hit_mock = MagicMock()
        hit_mock.id = "MISSING_M_1"
        hit_mock.accession = "ACC_M_NF"
        hit_mock.dbxrefs = []
        # retrieve_feature_id will fail
        loader.store_bio_searchio_hit(hit_mock, target="Blast")

    def test_multispecies_store_bio_searchio_hit_no_acc_and_go_fail(self):
        """Test multispecies store bio searchio hit no acc and go fail."""
        loader = MultispeciesFeatureLoader("SOURCE_HIT_X", "test.fa")
        hit_mock = MagicMock()
        hit_mock.id = "HIT_X_1"
        if hasattr(hit_mock, "accession"):
            del hit_mock.accession
        hit_mock.dbxrefs = ["GO:9999", "OTHER:O1"]
        loader.store_bio_searchio_hit(hit_mock, target="Blast")
        self.assertIn("GO:9999", loader.ignored_goterms)
        feat = Feature.objects.get(uniquename="HIT_X_1")
        self.assertTrue(
            FeatureDbxref.objects.filter(feature=feat, dbxref__accession="O1").exists()
        )

    def test_store_feature_publication(self):
        """Test store feature publication."""
        loader = FeatureLoader("GFF_PUB", "test.gff", self.org)
        self.create_feat("f_pub_1", self.cvterm_poly)
        db_doi = Db.objects.get_or_create(name="DOI")[0]
        dbxref_doi = Dbxref.objects.get_or_create(
            db=db_doi, accession="10.1234/test_pub_1"
        )[0]
        null_cvterm = Cvterm.objects.get(name="null", cv__name="null")
        pub = Pub.objects.create(
            uniquename="pub_unique_1", type=null_cvterm, is_obsolete=False
        )
        PubDbxref.objects.create(pub=pub, dbxref=dbxref_doi, is_current=True)
        loader.store_feature_publication("f_pub_1", "polypeptide", "10.1234/test_pub_1")
        self.assertTrue(
            Feature.objects.get(
                uniquename="f_pub_1"
            ).FeaturePub_feature_Feature.exists()
        )

    @patch("machado.loaders.feature.FeatureAttributesLoader")
    def test_store_tabix_VCF_feature_success(self, MockAttrLoader):
        """Test store tabix VCF feature success."""
        loader = FeatureLoader("VCF_S", "test.vcf", self.org)
        tabix_feat = MagicMock()
        tabix_feat.id = "VAR_S_1"
        tabix_feat.ref = "A"
        tabix_feat.alt = "T,G"
        tabix_feat.pos = 100
        tabix_feat.qual = "50"
        tabix_feat.info = "VC=SNP"
        tabix_feat.contig = "CONTIG_VCF_S"
        mock_attrs = MockAttrLoader.return_value
        mock_attrs.get_attributes.return_value = {"vc": "SNP"}
        db_fasta = Db.objects.get_or_create(name="FASTA_SOURCE")[0]
        dbxref_contig = Dbxref.objects.get_or_create(
            db=db_fasta, accession="CONTIG_VCF_S"
        )[0]
        self.create_feat(
            "CONTIG_VCF_S",
            self.ensure_cvterm("chromosome", self.cv_seq),
            dbxref=dbxref_contig,
        )
        self.ensure_cvterm("SNP", self.cv_seq)
        Cvterm.objects.get_or_create(
            name="quality_value",
            cv=self.cv_seq,
            defaults={
                "dbxref": Dbxref.objects.create(
                    db=self.db_internal, accession="qual_acc_v_s"
                ),
                "is_obsolete": 0,
                "is_relationshiptype": 0,
            },
        )
        loader.store_tabix_VCF_feature(tabix_feat)
        self.assertTrue(Feature.objects.filter(uniquename="VAR_S_1").exists())
        self.assertEqual(
            Featureloc.objects.filter(feature__uniquename="VAR_S_1").count(), 3
        )

    @patch("machado.loaders.feature.FeatureAttributesLoader")
    def test_store_tabix_VCF_feature_missing_type(self, MockAttrLoader):
        """Test store tabix VCF feature missing type."""
        loader = FeatureLoader("VCF_MT", "test.vcf", self.org)
        tabix_feat = MagicMock()
        tabix_feat.info = "OTHER=VALUE"
        mock_attrs = MockAttrLoader.return_value
        mock_attrs.get_attributes.return_value = {"other": "value"}
        with self.assertRaisesRegex(ImportingError, "Impossible to get the attribute"):
            loader.store_tabix_VCF_feature(tabix_feat)

    @patch("machado.loaders.feature.FeatureAttributesLoader")
    def test_store_tabix_VCF_feature_pub_and_loc_ie(self, MockAttrLoader):
        """Test store tabix VCF feature pub and loc ie."""
        db_doi = Db.objects.get_or_create(name="DOI")[0]
        dbxref_doi = Dbxref.objects.get_or_create(
            db=db_doi, accession="10.1234/vcf_doi"
        )[0]
        # Trigger initialization of null objects
        FeatureLoaderBase("VCF", "dummy.vcf")
        null_cvterm = Cvterm.objects.get(name="null", cv__name="null")
        pub = Pub.objects.create(
            uniquename="vcf_pub", type=null_cvterm, is_obsolete=False
        )
        PubDbxref.objects.create(pub=pub, dbxref=dbxref_doi, is_current=True)

        loader = FeatureLoader("VCF_IE", "test.vcf", self.org, doi="10.1234/vcf_doi")
        tabix_feat = MagicMock()
        tabix_feat.id = "VAR_IE"
        tabix_feat.ref = "A"
        tabix_feat.alt = "T"
        tabix_feat.pos = 100
        tabix_feat.qual = "."
        tabix_feat.info = "VC=SNP"
        tabix_feat.contig = "C1"
        mock_attrs = MockAttrLoader.return_value
        mock_attrs.get_attributes.return_value = {"vc": "SNP"}
        db_fasta = Db.objects.get_or_create(name="FASTA_SOURCE")[0]
        dbxref_c1 = Dbxref.objects.get_or_create(db=db_fasta, accession="C1")[0]
        self.create_feat(
            "C1",
            self.ensure_cvterm("chromosome", self.cv_seq),
            dbxref=dbxref_c1,
        )
        self.ensure_cvterm("SNP", self.cv_seq)

        with patch(
            "machado.models.FeaturePub.objects.get_or_create",
            side_effect=IntegrityError("Pub IE"),
        ):
            with self.assertRaises(ImportingError):
                loader.store_tabix_VCF_feature(tabix_feat)

        with patch(
            "machado.models.Featureloc.objects.get_or_create",
            side_effect=IntegrityError("Loc IE"),
        ):
            with self.assertRaises(ImportingError):
                loader.store_tabix_VCF_feature(tabix_feat)

    def test_store_feature_pairs(self):
        """Test store feature pairs."""
        loader = FeatureLoader("GFF_PAIR", "test.gff", self.org)
        mRNA_type = self.ensure_cvterm("mRNA_P", self.cv_seq)
        self.ensure_cvterm("located in", self.cv_rel)
        f1 = self.create_feat("f_pair_1", mRNA_type)
        f2 = self.create_feat("f_pair_2", mRNA_type)
        loader.store_feature_pairs(
            ["f_pair_1", "f_pair_2"], self.cvterm_poly, soterm="mRNA_P"
        )
        self.assertTrue(
            FeatureRelationship.objects.filter(
                subject=f1, object=f2, type=self.cvterm_poly
            ).exists()
        )

    @patch("machado.loaders.feature.FeatureAttributesLoader")
    def test_store_feature_annotation(self, MockAttrLoader):
        """Test store feature annotation."""
        loader = FeatureLoader("GFF_ANN", "test.gff", self.org)
        mRNA_type = self.ensure_cvterm("mRNA_A", self.cv_seq)
        self.create_feat("f_ann_1", mRNA_type)
        mock_attrs = MockAttrLoader.return_value
        mock_attrs.get_attributes.return_value = {"note": "test annotation"}
        loader.store_feature_annotation(
            "f_ann_1", "mRNA_A", "note", "test annotation", doi=None
        )
        mock_attrs.process_attributes.assert_called()

    def test_store_feature_dbxref_invalid(self):
        """Test store feature dbxref invalid."""
        loader = FeatureLoader("GFF_DBX_I", "test.gff", self.org)
        mRNA_type = self.ensure_cvterm("mRNA_DI", self.cv_seq)
        self.create_feat("f_dbx_inv_1", mRNA_type)
        with self.assertRaisesRegex(ImportingError, "Incorrect DBxRef"):
            loader.store_feature_dbxref("f_dbx_inv_1", "mRNA_DI", "INVALID_DBX")

    def test_store_tabix_GFF_feature_parent_not_found(self):
        """Test store tabix GFF feature parent not found."""
        loader = FeatureLoader("GFF_PNF", "test.gff", self.org)
        tabix_mock = MagicMock()
        tabix_mock.contig = "UNKNOWN_CONTIG"
        with self.assertRaises(ImportingError):
            loader.store_tabix_GFF_feature(tabix_mock, qtl=False)

    @patch("machado.loaders.feature.FeatureAttributesLoader")
    def test_store_tabix_GFF_feature_with_doi(self, MockAttrLoader):
        """Test store tabix GFF feature with doi."""
        db_doi = Db.objects.get_or_create(name="DOI")[0]
        dbxref_doi = Dbxref.objects.get_or_create(db=db_doi, accession="10.1000/1")[0]
        null_db = Db.objects.get_or_create(name="null_test")[0]
        null_dbx = Dbxref.objects.get_or_create(db=null_db, accession="null_test")[0]
        null_cv = Cv.objects.get_or_create(name="null_test")[0]
        null_cvterm = Cvterm.objects.get_or_create(
            name="null_test",
            cv=null_cv,
            dbxref=null_dbx,
            is_obsolete=0,
            is_relationshiptype=0,
        )[0]
        pub = Pub.objects.create(uniquename="pub_doi", type=null_cvterm)
        pub_dbxref = PubDbxref.objects.create(
            pub=pub, dbxref=dbxref_doi, is_current=True
        )

        loader = FeatureLoader("GFF_DOI", "test.gff", self.org)
        loader.pub_dbxref_doi = pub_dbxref

        # Mocking tabix feature and its contig
        tabix_mock = MagicMock()
        tabix_mock.contig = "CONTIG_DOI"
        tabix_mock.id = "FEAT_DOI"
        tabix_mock.feature = "gene"
        tabix_mock.start = 10
        tabix_mock.end = 100
        tabix_mock.strand = "+"
        tabix_mock.frame = "."

        db_fasta = Db.objects.get_or_create(name="FASTA_SOURCE")[0]
        dbxref_contig = Dbxref.objects.create(db=db_fasta, accession="CONTIG_DOI")
        mRNA_type = self.ensure_cvterm("mRNA", self.cv_seq)
        self.ensure_cvterm("gene", self.cv_seq)
        self.create_feat("CONTIG_DOI", mRNA_type, dbxref=dbxref_contig)

        mock_attrs = MockAttrLoader.return_value
        mock_attrs.get_attributes.return_value = {"id": "FEAT_DOI"}

        loader.store_tabix_GFF_feature(tabix_mock, qtl=False)
        feat = Feature.objects.get(uniquename="FEAT_DOI")
        self.assertTrue(feat.FeaturePub_feature_Feature.exists())

    @patch("machado.loaders.feature.FeatureAttributesLoader")
    def test_store_tabix_GFF_feature_location_integrity_error(self, MockAttrLoader):
        """Test store tabix GFF feature location integrity error."""
        loader = FeatureLoader("GFF_LOC_IE", "test.gff", self.org)
        tabix_mock = MagicMock()
        tabix_mock.contig = "CONTIG_LOC"
        tabix_mock.id = "FEAT_LOC"
        tabix_mock.feature = "gene"
        tabix_mock.start = 10
        tabix_mock.end = 100
        tabix_mock.strand = "+"
        tabix_mock.frame = "."

        db_fasta = Db.objects.get_or_create(name="FASTA_SOURCE")[0]
        dbxref_contig = Dbxref.objects.create(db=db_fasta, accession="CONTIG_LOC")
        mRNA_type = self.ensure_cvterm("mRNA", self.cv_seq)
        self.ensure_cvterm("gene", self.cv_seq)
        self.create_feat("CONTIG_LOC", mRNA_type, dbxref=dbxref_contig)

        # Mock process_attributes to do nothing
        mock_attrs = MockAttrLoader.return_value
        mock_attrs.get_attributes.return_value = {"id": "FEAT_DOI"}

        # First call success
        loader.store_tabix_GFF_feature(tabix_mock, qtl=False)

        with patch(
            "machado.models.Featureloc.objects.get_or_create",
            side_effect=IntegrityError("conflicting location"),
        ):
            with self.assertRaises(ImportingError):
                loader.store_tabix_GFF_feature(tabix_mock, qtl=False)

    @patch("machado.loaders.feature.FeatureAttributesLoader")
    def test_store_tabix_VCF_feature_so_term_missing(self, MockAttrLoader):
        """Test store tabix VCF feature so term missing."""
        loader = FeatureLoader("VCF_SO", "test.vcf", self.org)
        tabix_mock = MagicMock()
        tabix_mock.id = "VCF_1"
        tabix_mock.ref = "A"
        tabix_mock.alt = "T"
        mock_attrs = MockAttrLoader.return_value
        mock_attrs.get_attributes.return_value = {"vc": "nonexistent_so_term"}

        with self.assertRaisesRegex(
            ImportingError, r"\(sequence\).*ontology term not found"
        ):
            loader.store_tabix_VCF_feature(tabix_mock)
