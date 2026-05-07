# Copyright 2018 by Embrapa.  All rights reserved.
#
# This code is part of the machado distribution and governed by its
# license. Please see the LICENSE.txt and README.md files that should
# have been included as part of this package for licensing information.

"""Tests for API load views."""

from unittest.mock import patch, mock_open
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status

from machado.api.views.load import (
    OrganismViewSet,
    RelationsOntologyViewSet,
    PublicationViewSet,
    SequenceOntologyViewSet,
    GeneOntologyViewSet,
    FastaViewSet,
    FeatureAnnotationViewSet,
    FeatureSequenceViewSet,
    FeaturePublicationViewSet,
    FeatureDBxRefViewSet,
    GFFViewSet,
)


class BaseLoadViewSetTest(TestCase):
    """Test suite for BaseLoadViewSet."""

    def setUp(self):
        """Set up test context."""
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            username="testuser", password="password"
        )


class OrganismViewSetTest(BaseLoadViewSetTest):
    """Test suite for OrganismViewSet."""

    @patch("machado.api.views.load.Thread")
    def test_create_success(self, mock_thread):
        """Test create success."""
        view = OrganismViewSet.as_view({"post": "create"})
        data = {
            "genus": "Genus",
            "species": "species",
            "abbreviation": "G.s",
            "common_name": "Common",
            "infraspecific_name": "infra",
            "comment": "comment",
        }
        request = self.factory.post("/api/load/organism", data)
        force_authenticate(request, user=self.user)
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "Submited successfully")
        mock_thread.assert_called_once()
        # Check thread target and kwargs
        call_kwargs = mock_thread.call_args.kwargs
        self.assertEqual(call_kwargs["args"], ("insert_organism",))
        self.assertEqual(call_kwargs["kwargs"]["genus"], "Genus")

    def test_create_missing_params(self):
        """Test create missing params."""
        view = OrganismViewSet.as_view({"post": "create"})
        request = self.factory.post("/api/load/organism", {"genus": "Genus"})
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("machado.api.views.load.Thread")
    def test_destroy_success(self, mock_thread):
        """Test destroy success."""
        view = OrganismViewSet.as_view({"delete": "destroy"})
        request = self.factory.delete("/api/load/organism")
        force_authenticate(request, user=self.user)
        response = view(request, organism="Genus Species")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        mock_thread.assert_called_once()
        self.assertEqual(
            mock_thread.call_args.kwargs["args"], ("remove_organism",)
        )
        self.assertEqual(
            mock_thread.call_args.kwargs["kwargs"],
            {"organism": "Genus Species"},
        )


class RelationsOntologyViewSetTest(BaseLoadViewSetTest):
    """Test suite for RelationsOntologyViewSet."""

    @patch("machado.api.views.load.Thread")
    @patch("builtins.open", new_callable=mock_open)
    def test_create_success(self, mock_file, mock_thread):
        """Test create success."""
        view = RelationsOntologyViewSet.as_view({"post": "create"})
        file_content = b"test content"
        uploaded_file = SimpleUploadedFile("ro.obo", file_content)

        request = self.factory.post(
            "/api/load/relations_ontology",
            {"file": uploaded_file},
            format="multipart",
        )
        force_authenticate(request, user=self.user)
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_thread.assert_called_once()
        self.assertEqual(
            mock_thread.call_args.kwargs["args"], ("load_relations_ontology",)
        )
        mock_file.assert_called_with("/tmp/ro.obo", "wt")

    @patch("machado.api.views.load.Thread")
    def test_destroy_success(self, mock_thread):
        """Test destroy success."""
        view = RelationsOntologyViewSet.as_view({"delete": "destroy"})
        request = self.factory.delete(
            "/api/load/relations_ontology", {"name": "test_cv"}
        )
        force_authenticate(request, user=self.user)
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        mock_thread.assert_called_once()
        self.assertEqual(
            mock_thread.call_args.kwargs["args"], ("remove_ontology",)
        )

    def test_destroy_missing_name(self):
        """Test destroy missing name."""
        view = RelationsOntologyViewSet.as_view({"delete": "destroy"})
        request = self.factory.delete("/api/load/relations_ontology", {})
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class PublicationViewSetTest(BaseLoadViewSetTest):
    """Test suite for PublicationViewSet."""

    @patch("machado.api.views.load.Thread")
    @patch("builtins.open", new_callable=mock_open)
    def test_create_success(self, mock_file, mock_thread):
        """Test create success."""
        view = PublicationViewSet.as_view({"post": "create"})
        uploaded_file = SimpleUploadedFile("ref.bib", b"bibtex content")

        request = self.factory.post(
            "/api/load/publication",
            {"file": uploaded_file, "cpu": 4},
            format="multipart",
        )
        force_authenticate(request, user=self.user)
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_thread.assert_called_once()
        self.assertEqual(
            mock_thread.call_args.kwargs["args"], ("load_publication",)
        )
        self.assertEqual(mock_thread.call_args.kwargs["kwargs"]["cpu"], 4)

    def test_create_no_file(self):
        """Test create no file."""
        view = PublicationViewSet.as_view({"post": "create"})
        request = self.factory.post("/api/load/publication", {})
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class SequenceOntologyViewSetTest(BaseLoadViewSetTest):
    """Test suite for SequenceOntologyViewSet."""

    @patch("machado.api.views.load.Thread")
    @patch("builtins.open", new_callable=mock_open)
    def test_create_success(self, mock_file, mock_thread):
        """Test create success."""
        view = SequenceOntologyViewSet.as_view({"post": "create"})
        uploaded_file = SimpleUploadedFile("so.obo", b"so content")
        request = self.factory.post(
            "/api/load/sequence_ontology",
            {"file": uploaded_file},
            format="multipart",
        )
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_thread.assert_called_once()
        self.assertEqual(
            mock_thread.call_args.kwargs["args"], ("load_sequence_ontology",)
        )

    @patch("machado.api.views.load.Thread")
    def test_destroy_success(self, mock_thread):
        """Test destroy success."""
        view = SequenceOntologyViewSet.as_view({"delete": "destroy"})
        request = self.factory.delete(
            "/api/load/sequence_ontology", {"name": "so_cv"}
        )
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        mock_thread.assert_called_once()
        self.assertEqual(
            mock_thread.call_args.kwargs["args"], ("remove_ontology",)
        )

    def test_destroy_missing_name(self):
        """Test destroy missing name."""
        view = SequenceOntologyViewSet.as_view({"delete": "destroy"})
        request = self.factory.delete("/api/load/sequence_ontology", {})
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class GeneOntologyViewSetTest(BaseLoadViewSetTest):
    """Test suite for GeneOntologyViewSet."""

    @patch("machado.api.views.load.Thread")
    @patch("builtins.open", new_callable=mock_open)
    def test_create_success(self, mock_file, mock_thread):
        """Test create success."""
        view = GeneOntologyViewSet.as_view({"post": "create"})
        uploaded_file = SimpleUploadedFile("go.obo", b"go content")
        request = self.factory.post(
            "/api/load/gene_ontology",
            {"file": uploaded_file},
            format="multipart",
        )
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_thread.assert_called_once()
        self.assertEqual(
            mock_thread.call_args.kwargs["args"], ("load_gene_ontology",)
        )

    @patch("machado.api.views.load.Thread")
    def test_destroy_success(self, mock_thread):
        """Test destroy success."""
        view = GeneOntologyViewSet.as_view({"delete": "destroy"})
        request = self.factory.delete(
            "/api/load/gene_ontology", {"name": "go_cv"}
        )
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        mock_thread.assert_called_once()
        self.assertEqual(
            mock_thread.call_args.kwargs["args"], ("remove_ontology",)
        )

    def test_destroy_missing_name(self):
        """Test destroy missing name."""
        view = GeneOntologyViewSet.as_view({"delete": "destroy"})
        request = self.factory.delete("/api/load/gene_ontology", {})
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class FastaViewSetTest(BaseLoadViewSetTest):
    """Test suite for FastaViewSet."""

    @patch("machado.api.views.load.Thread")
    @patch("builtins.open", new_callable=mock_open)
    def test_create_success(self, mock_file, mock_thread):
        """Test create success."""
        view = FastaViewSet.as_view({"post": "create"})
        uploaded_file = SimpleUploadedFile("seq.fa", b">seq\nATGC")
        data = {
            "file": uploaded_file,
            "organism": "Test org",
            "soterm": "chromosome",
        }
        request = self.factory.post(
            "/api/load/fasta", data, format="multipart"
        )
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_thread.assert_called_once()
        self.assertEqual(mock_thread.call_args.kwargs["args"], ("load_fasta",))

    def test_create_no_file(self):
        """Test create no file."""
        view = FastaViewSet.as_view({"post": "create"})
        request = self.factory.post(
            "/api/load/fasta",
            {"organism": "org", "soterm": "chr"},
            format="multipart",
        )
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_missing_params(self):
        """Test create missing params."""
        view = FastaViewSet.as_view({"post": "create"})
        uploaded_file = SimpleUploadedFile("seq.fa", b"...")

        # Missing organism
        request = self.factory.post(
            "/api/load/fasta",
            {"file": uploaded_file, "soterm": "chr"},
            format="multipart",
        )
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Missing soterm
        request = self.factory.post(
            "/api/load/fasta",
            {"file": uploaded_file, "organism": "org"},
            format="multipart",
        )
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class FeatureAnnotationViewSetTest(BaseLoadViewSetTest):
    """Test suite for FeatureAnnotationViewSet."""

    @patch("machado.api.views.load.Thread")
    @patch("builtins.open", new_callable=mock_open)
    def test_create_success(self, mock_file, mock_thread):
        """Test create success."""
        view = FeatureAnnotationViewSet.as_view({"post": "create"})
        uploaded_file = SimpleUploadedFile("annot.tab", b"data")
        data = {
            "file": uploaded_file,
            "organism": "Test org",
            "soterm": "gene",
            "cvterm": "note",
        }
        request = self.factory.post(
            "/api/load/feature_annotation", data, format="multipart"
        )
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_thread.assert_called_once()
        self.assertEqual(
            mock_thread.call_args.kwargs["args"], ("load_feature_annotation",)
        )

    def test_create_missing_params(self):
        """Test create missing params."""
        view = FeatureAnnotationViewSet.as_view({"post": "create"})
        f = SimpleUploadedFile("f.tab", b"")
        cases = [
            ({"organism": "org", "soterm": "term"}, "cvterm"),
            ({"organism": "org", "cvterm": "term"}, "soterm"),
            ({"soterm": "term", "cvterm": "term"}, "organism"),
            ({}, "file"),
        ]
        for data, missing in cases:
            if missing != "file":
                data["file"] = f
            request = self.factory.post(
                "/api/load/feature_annotation", data, format="multipart"
            )
            force_authenticate(request, user=self.user)
            response = view(request)
            self.assertEqual(
                response.status_code,
                status.HTTP_400_BAD_REQUEST,
                f"Failed for missing {missing}",
            )


class FeatureSequenceViewSetTest(BaseLoadViewSetTest):
    """Test suite for FeatureSequenceViewSet."""

    @patch("machado.api.views.load.Thread")
    @patch("builtins.open", new_callable=mock_open)
    def test_create_success(self, mock_file, mock_thread):
        """Test create success."""
        view = FeatureSequenceViewSet.as_view({"post": "create"})
        uploaded_file = SimpleUploadedFile("seqs.fa", b"data")
        data = {
            "file": uploaded_file,
            "organism": "Test org",
            "soterm": "transcript",
        }
        request = self.factory.post(
            "/api/load/feature_sequence", data, format="multipart"
        )
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_thread.assert_called_once()
        self.assertEqual(
            mock_thread.call_args.kwargs["args"], ("load_feature_sequence",)
        )

    def test_create_missing_params(self):
        """Test create missing params."""
        view = FeatureSequenceViewSet.as_view({"post": "create"})
        f = SimpleUploadedFile("f.fa", b"")
        cases = [
            ({"organism": "org"}, "soterm"),
            ({"soterm": "term"}, "organism"),
            ({}, "file"),
        ]
        for data, missing in cases:
            if missing != "file":
                data["file"] = f
            request = self.factory.post(
                "/api/load/feature_sequence", data, format="multipart"
            )
            force_authenticate(request, user=self.user)
            response = view(request)
            self.assertEqual(
                response.status_code,
                status.HTTP_400_BAD_REQUEST,
                f"Failed for missing {missing}",
            )


class FeaturePublicationViewSetTest(BaseLoadViewSetTest):
    """Test suite for FeaturePublicationViewSet."""

    @patch("machado.api.views.load.Thread")
    @patch("builtins.open", new_callable=mock_open)
    def test_create_success(self, mock_file, mock_thread):
        """Test create success."""
        view = FeaturePublicationViewSet.as_view({"post": "create"})
        uploaded_file = SimpleUploadedFile("pubs.tab", b"data")
        request = self.factory.post(
            "/api/load/feature_publication",
            {"file": uploaded_file},
            format="multipart",
        )
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_thread.assert_called_once()
        self.assertEqual(
            mock_thread.call_args.kwargs["args"], ("load_feature_publication",)
        )

    def test_create_no_file(self):
        """Test create no file."""
        view = FeaturePublicationViewSet.as_view({"post": "create"})
        request = self.factory.post(
            "/api/load/feature_publication", {}, format="multipart"
        )
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class FeatureDBxRefViewSetTest(BaseLoadViewSetTest):
    """Test suite for FeatureDBxRefViewSet."""

    @patch("machado.api.views.load.Thread")
    @patch("builtins.open", new_callable=mock_open)
    def test_create_success(self, mock_file, mock_thread):
        """Test create success."""
        view = FeatureDBxRefViewSet.as_view({"post": "create"})
        uploaded_file = SimpleUploadedFile("dbxrefs.tab", b"data")
        data = {
            "file": uploaded_file,
            "organism": "Test org",
            "soterm": "gene",
        }
        request = self.factory.post(
            "/api/load/feature_dbxrefs", data, format="multipart"
        )
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_thread.assert_called_once()
        self.assertEqual(
            mock_thread.call_args.kwargs["args"], ("load_feature_dbxrefs",)
        )

    def test_create_missing_params(self):
        """Test create missing params."""
        view = FeatureDBxRefViewSet.as_view({"post": "create"})
        f = SimpleUploadedFile("f.tab", b"")
        cases = [
            ({"organism": "org"}, "soterm"),
            ({"soterm": "term"}, "organism"),
            ({}, "file"),
        ]
        for data, missing in cases:
            if missing != "file":
                data["file"] = f
            request = self.factory.post(
                "/api/load/feature_dbxrefs", data, format="multipart"
            )
            force_authenticate(request, user=self.user)
            response = view(request)
            self.assertEqual(
                response.status_code,
                status.HTTP_400_BAD_REQUEST,
                f"Failed for missing {missing}",
            )


class GFFViewSetTest(BaseLoadViewSetTest):
    """Test suite for GFFViewSet."""

    @patch("machado.api.views.load.Thread")
    @patch("builtins.open", new_callable=mock_open)
    def test_create_success(self, mock_file, mock_thread):
        """Test create success."""
        view = GFFViewSet.as_view({"post": "create"})
        gff = SimpleUploadedFile("test.gff", b"data")
        tbi = SimpleUploadedFile("test.gff.tbi", b"data")
        data = {"file": gff, "tbiFile": tbi, "organism": "Test org"}
        request = self.factory.post("/api/load/gff", data, format="multipart")
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_thread.assert_called_once()
        self.assertEqual(mock_thread.call_args.kwargs["args"], ("load_gff",))

    def test_create_missing_params(self):
        """Test create missing params."""
        view = GFFViewSet.as_view({"post": "create"})
        f = SimpleUploadedFile("f.gff", b"")
        cases = [
            ({"tbiFile": f, "organism": "org"}, "file"),
            ({"file": f, "organism": "org"}, "tbiFile"),
            ({"file": f, "tbiFile": f}, "organism"),
        ]
        for data, missing in cases:
            request = self.factory.post(
                "/api/load/gff", data, format="multipart"
            )
            force_authenticate(request, user=self.user)
            response = view(request)
            self.assertEqual(
                response.status_code,
                status.HTTP_400_BAD_REQUEST,
                f"Failed for missing {missing}",
            )

    def test_destroy_no_file(self):
        """Test destroy no file."""
        view = GFFViewSet.as_view({"delete": "destroy"})
        request = self.factory.delete("/api/load/gff", {})
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("machado.api.views.load.Thread")
    def test_destroy_success(self, mock_thread):
        """Test destroy success."""
        view = GFFViewSet.as_view({"delete": "destroy"})
        request = self.factory.delete("/api/load/gff", {"file": "test.gff"})
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        mock_thread.assert_called_once()
        self.assertEqual(
            mock_thread.call_args.kwargs["args"], ("remove_file",)
        )
