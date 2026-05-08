# Copyright 2018 by Embrapa.  All rights reserved.
#
# This code is part of the machado distribution and governed by its
# license. Please see the LICENSE.txt and README.md files that should
# have been included as part of this package for licensing information.

"""Tests for organism loader."""

from django.test import TestCase
from machado.loaders.organism import OrganismLoader
from machado.loaders.exceptions import ImportingError
from machado.models import (
    Organism,
    Db,
    Dbxref,
    Pub,
    PubDbxref,
    OrganismPub,
    OrganismDbxref,
    Organismprop,
)


class OrganismLoaderTest(TestCase):
    """Test suite for OrganismLoader."""

    def setUp(self):
        """Set up test context."""
        # Create required metadata for loader init
        self.loader = OrganismLoader()

    def test_init_with_db(self):
        """Test init with db."""
        OrganismLoader(organism_db="TAXONOMY")
        self.assertTrue(Db.objects.filter(name="TAXONOMY").exists())

    def test_parse_scientific_name(self):
        """Test parse scientific name."""
        # Case 1: Genus species
        self.assertEqual(
            self.loader.parse_scientific_name("Genus species"),
            ("Genus", "species", None),
        )
        # Case 2: Genus species infra
        self.assertEqual(
            self.loader.parse_scientific_name("Genus species infra"),
            ("Genus", "species", "Genus species infra"),
        )
        # Case 3: Only genus
        self.assertEqual(
            self.loader.parse_scientific_name("Genus"), ("Genus", ".spp", None)
        )

    def test_store_organism_record(self):
        """Test store organism record."""
        loader = OrganismLoader(organism_db="NCBI")
        loader.store_organism_record(
            taxid="1234",
            scname="Genus species",
            synonyms=["Syn1"],
            common_names=["Common1", "Common2"],
        )

        org = Organism.objects.get(genus="Genus", species="species")
        self.assertEqual(org.common_name, "Common1,Common2")
        self.assertEqual(org.abbreviation, "G. species")

        # Check Dbxref
        self.assertTrue(
            OrganismDbxref.objects.filter(
                organism=org, dbxref__accession="1234"
            ).exists()
        )

        # Check Synonym
        self.assertTrue(
            Organismprop.objects.filter(organism=org, value="Syn1").exists()
        )

    def test_store_organism_publication(self):
        """Test store organism publication."""
        org = Organism.objects.create(genus="Genus", species="species")
        db_doi = Db.objects.create(name="DOI")
        dbxref_doi = Dbxref.objects.create(db=db_doi, accession="10.1234/test")
        pub = Pub.objects.create(
            uniquename="test_pub", type_id=self.loader.cvterm_synonym.cvterm_id
        )  # Using any cvterm for pub type
        PubDbxref.objects.create(pub=pub, dbxref=dbxref_doi, is_current=True)

        self.loader.store_organism_publication("Genus species", "10.1234/test")

        self.assertTrue(OrganismPub.objects.filter(organism=org, pub=pub).exists())

    def test_store_organism_publication_not_found(self):
        """Test store organism publication not found."""
        Organism.objects.create(genus="Genus", species="species")
        with self.assertRaisesRegex(ImportingError, "not registered"):
            self.loader.store_organism_publication(
                "Genus species", "10.1234/nonexistent"
            )
