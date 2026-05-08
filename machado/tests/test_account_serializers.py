"""Module tests."""

from django.test import TestCase
from django.contrib.auth.models import User
from machado.account.serializers import UserSerializer, UserCreateSerializer


class UserSerializerTest(TestCase):
    """Test suite for UserSerializer."""

    def setUp(self):
        """Set up test context."""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="password123",
        )

    def test_user_serializer(self):
        """Test user serializer."""
        serializer = UserSerializer(self.user)
        self.assertEqual(serializer.data["username"], "testuser")
        self.assertEqual(serializer.data["email"], "test@example.com")


class UserCreateSerializerTest(TestCase):
    """Test suite for UserCreateSerializer."""

    def test_create_valid_user(self):
        """Test create valid user."""
        data = {
            "username": "newuser",
            "email": "new@example.com",
            "password": "newpassword123",
            "first_name": "New",
            "last_name": "User",
        }
        serializer = UserCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        self.assertEqual(user.username, "newuser")
        self.assertEqual(user.email, "new@example.com")

    def test_create_invalid_username(self):
        """Test create invalid username."""
        User.objects.create_user(
            username="existinguser",
            email="existing1@example.com",
            password="pwd",
        )
        data = {
            "username": "existinguser",
            "email": "new@example.com",
            "password": "newpassword123",
        }
        serializer = UserCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("username", serializer.errors)

    def test_create_invalid_email(self):
        """Test create invalid email."""
        User.objects.create_user(
            username="existinguser",
            email="existing@example.com",
            password="pwd",
        )
        data = {
            "username": "newuser",
            "email": "existing@example.com",
            "password": "newpassword123",
        }
        serializer = UserCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)
