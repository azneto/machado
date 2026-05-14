# Copyright 2018 by Embrapa.  All rights reserved.
#
# This code is part of the machado distribution and governed by its
# license. Please see the LICENSE.txt and README.md files that should
# have been included as part of this package for licensing information.

"""Tests for loaders common library."""

import os
import gzip
import tempfile
from django.test import TestCase
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from machado.loaders.common import (
    FileValidator,
    FieldsValidator,
    get_num_lines,
    insert_organism,
    retrieve_organism,
    retrieve_feature_id,
    retrieve_cvterm,
)
from machado.loaders.exceptions import ImportingError
from machado.models import (
    Organism,
    Feature,
    Cv,
    Cvterm,
    Dbxref,
    Db,
    FeatureDbxref,
    Cvtermsynonym,
)


class FileValidatorTest(TestCase):
    """Test suite for FileValidator."""

    def setUp(self):
        """Set up test context."""
        self.validator = FileValidator()
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_file.close()

    def tearDown(self):
        """tearDown."""
        if os.path.exists(self.temp_file.name):
            os.remove(self.temp_file.name)

    def test_validate_success(self):
        """Test validate success."""
        self.validator.validate(self.temp_file.name)

    def test_exists_fail(self):
        """Test exists fail."""
        with self.assertRaisesRegex(ImportingError, "does not exist"):
            self.validator.validate("non_existent_file")

    def test_is_file_fail(self):
        """Test is file fail."""
        temp_dir = tempfile.mkdtemp()
        try:
            with self.assertRaisesRegex(ImportingError, "is not a file"):
                self.validator.validate(temp_dir)
        finally:
            os.rmdir(temp_dir)

    def test_is_readable_fail(self):
        """Test is readable fail."""
        os.chmod(self.temp_file.name, 0o000)
        # On some systems/CI environments, root might still be able to read.
        # But we try.
        try:
            # If it doesn't raise, it's probably because of permissions in the
            # env
            self.validator.validate(self.temp_file.name)
        except ImportingError:
            pass
        finally:
            os.chmod(self.temp_file.name, 0o666)


class FieldsValidatorTest(TestCase):
    """Test suite for FieldsValidator."""

    def setUp(self):
        """Set up test context."""
        self.validator = FieldsValidator()

    def test_validate_success(self):
        """Test validate success."""
        self.validator.validate(2, ["f1", "f2"])

    def test_nfields_fail(self):
        """Test nfields fail."""
        with self.assertRaisesRegex(ImportingError, "differ from"):
            self.validator.validate(3, ["f1", "f2"])

    def test_nullfields_fail(self):
        """Test nullfields fail."""
        with self.assertRaisesRegex(ImportingError, "Found null or empty field"):
            self.validator.validate(2, ["f1", ""])
        with self.assertRaisesRegex(ImportingError, "Found null or empty field"):
            self.validator.validate(2, ["f1", None])


class UtilsTest(TestCase):
    """Test suite for Utils."""

    def test_get_num_lines(self):
        """Test get num lines."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("line1\n#comment\nline2\n")
            temp_name = f.name
        try:
            self.assertEqual(get_num_lines(temp_name), 2)
        finally:
            os.remove(temp_name)

    def test_get_num_lines_gz(self):
        """Test get num lines gz."""
        with tempfile.NamedTemporaryFile(suffix=".gz", delete=False) as f:
            temp_name = f.name
        try:
            with gzip.open(temp_name, "wt") as f:
                f.write("line1\n#comment\nline2\n")
            self.assertEqual(get_num_lines(temp_name), 2)
        finally:
            os.remove(temp_name)


class OrganismUtilsTest(TestCase):
    """Test suite for OrganismUtils."""

    def test_insert_organism_success(self):
        """Test insert organism success."""
        insert_organism(genus="Genus", species="species")
        self.assertTrue(
            Organism.objects.filter(genus="Genus", species="species").exists()
        )

    def test_insert_organism_already_exists(self):
        """Test insert organism already exists."""
        Organism.objects.create(genus="Genus", species="species")
        with self.assertRaisesRegex(ImportingError, "already registered"):
            insert_organism(genus="Genus", species="species")

    def test_retrieve_organism_success(self):
        """Test retrieve organism success."""
        Organism.objects.create(genus="Genus", species="species")
        obj = retrieve_organism("Genus species")
        self.assertEqual(obj.genus, "Genus")

    def test_retrieve_organism_infraspecific(self):
        """Test retrieve organism infraspecific."""
        Organism.objects.create(
            genus="Genus", species="species", infraspecific_name="infra name"
        )
        obj = retrieve_organism("Genus species infra name")
        self.assertEqual(obj.infraspecific_name, "infra name")

    def test_retrieve_organism_fail(self):
        """Test retrieve organism fail."""
        with self.assertRaisesRegex(ObjectDoesNotExist, "not registered"):
            retrieve_organism("Unknown species")


class FeatureUtilsTest(TestCase):
    """Test suite for FeatureUtils."""

    def setUp(self):
        """Set up test context."""
        self.db = Db.objects.create(name="test_db")
        self.dbxref = Dbxref.objects.create(db=self.db, accession="acc1", version="1")
        self.cv_seq = Cv.objects.create(name="sequence")
        self.type_gene = Cvterm.objects.create(
            name="gene",
            cv=self.cv_seq,
            dbxref=self.dbxref,
            is_obsolete=0,
            is_relationshiptype=0,
        )
        self.org = Organism.objects.create(genus="Genus", species="species")
        self.feature = Feature.objects.create(
            organism=self.org,
            uniquename="feat1",
            name="Feat One",
            type=self.type_gene,
            is_analysis=False,
            is_obsolete=False,
            timeaccessioned="2023-01-01T00:00:00Z",
            timelastmodified="2023-01-01T00:00:00Z",
            dbxref=self.dbxref,
        )

    def test_retrieve_feature_id_uniquename(self):
        """Test retrieve feature id uniquename."""
        fid = retrieve_feature_id("feat1", "gene", self.org)
        self.assertEqual(fid, self.feature.feature_id)

    def test_retrieve_feature_id_prefixed(self):
        """Test retrieve feature id prefixed."""
        self.feature.uniquename = "gene-feat2"
        self.feature.save()
        fid = retrieve_feature_id("feat2", "gene", self.org)
        self.assertEqual(fid, self.feature.feature_id)

    def test_retrieve_feature_id_name(self):
        """Test retrieve feature id name."""
        fid = retrieve_feature_id("Feat One", "gene", self.org)
        self.assertEqual(fid, self.feature.feature_id)

    def test_retrieve_feature_id_dbxref(self):
        """Test retrieve feature id dbxref."""
        fid = retrieve_feature_id("acc1", "gene", self.org)
        self.assertEqual(fid, self.feature.feature_id)

    def test_retrieve_feature_id_featuredbxref(self):
        """Test retrieve feature id featuredbxref."""
        dbxref2 = Dbxref.objects.create(db=self.db, accession="acc2", version="1")
        FeatureDbxref.objects.create(
            feature=self.feature, dbxref=dbxref2, is_current=True
        )
        fid = retrieve_feature_id("acc2", "gene", self.org)
        self.assertEqual(fid, self.feature.feature_id)

    def test_retrieve_feature_id_multiple_objects(self):
        """Test retrieve feature id multiple objects."""
        Feature.objects.create(
            organism=self.org,
            uniquename="feat2",
            name="Feat One",
            type=self.type_gene,
            is_analysis=False,
            is_obsolete=False,
            timeaccessioned="2023-01-01T00:00:00Z",
            timelastmodified="2023-01-01T00:00:00Z",
        )
        with self.assertRaises(MultipleObjectsReturned):
            retrieve_feature_id("Feat One", "gene", self.org)

    def test_retrieve_feature_id_not_found(self):
        """Test retrieve feature id not found."""
        with self.assertRaisesRegex(ObjectDoesNotExist, "does not exist"):
            retrieve_feature_id("unknown", "gene", self.org)


class CvtermUtilsTest(TestCase):
    """Test suite for CvtermUtils."""

    def setUp(self):
        """Set up test context."""
        self.db = Db.objects.create(name="test_db")
        self.dbxref = Dbxref.objects.create(db=self.db, accession="acc1", version="1")
        self.cv = Cv.objects.create(name="test_cv")
        self.term = Cvterm.objects.create(
            name="term1",
            cv=self.cv,
            dbxref=self.dbxref,
            is_obsolete=0,
            is_relationshiptype=0,
        )

    def test_retrieve_cvterm_success(self):
        """Test retrieve cvterm success."""
        obj = retrieve_cvterm("test_cv", "term1")
        self.assertEqual(obj, self.term)

    def test_retrieve_cvterm_synonym(self):
        """Test retrieve cvterm synonym."""
        Cvtermsynonym.objects.create(cvterm=self.term, synonym="syn1")
        obj = retrieve_cvterm("test_cv", "syn1")
        self.assertEqual(obj, self.term)

    def test_retrieve_cvterm_fail(self):
        """Test retrieve cvterm fail."""
        with self.assertRaisesRegex(
            ImportingError, r"\(test_cv\).*ontology term not found"
        ):
            retrieve_cvterm("test_cv", "unknown")
