from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token


@override_settings(ROOT_URLCONF='machado.account.urls')
class AccountViewsTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )
        self.admin = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="adminpassword"
        )
        self.token = Token.objects.create(user=self.user)
        self.admin_token = Token.objects.create(user=self.admin)

    def test_login_success(self):
        response = self.client.post("/login", {"email": "test@example.com", "password": "password123"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)

    def test_login_missing_fields(self):
        response = self.client.post("/login", {"email": "test@example.com"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_invalid_credentials(self):
        response = self.client.post("/login", {"email": "test@example.com", "password": "wrongpassword"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    def test_login_user_not_exist(self):
        response = self.client.post("/login", {"email": "notfound@example.com", "password": "wrongpassword"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_success(self):
        self.client.force_authenticate(user=self.user, token=self.token)
        response = self.client.post("/logout")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Token.objects.filter(user=self.user).exists())

    def test_logout_no_token(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post("/logout")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_list_users(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_admin_list_user_by_id(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(f"/{self.user.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "testuser")

    def test_admin_list_user_by_id_not_found(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(f"/9999")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_list_user_by_username(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(f"/username/testuser")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["username"], "testuser")

    def test_admin_list_user_by_username_not_found(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(f"/username/notfounduser")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_admin_create_user(self):
        self.client.force_authenticate(user=self.admin)
        data = {
            "username": "newuser",
            "email": "new@example.com",
            "password": "newpassword123",
            "first_name": "New",
            "last_name": "User",
        }
        response = self.client.post("/", data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_admin_create_user_invalid(self):
        self.client.force_authenticate(user=self.admin)
        data = {
            "username": "testuser", # Already exists
            "email": "new@example.com",
            "password": "newpassword123",
        }
        response = self.client.post("/", data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_update_user(self):
        self.client.force_authenticate(user=self.admin)
        data = {
            "first_name": "Updated",
            "is_staff": 1
        }
        response = self.client.put(f"/{self.user.id}", data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Updated")
        self.assertTrue(self.user.is_staff)

    def test_admin_update_user_not_found(self):
        self.client.force_authenticate(user=self.admin)
        data = {
            "first_name": "Updated",
        }
        response = self.client.put(f"/9999", data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_delete_user(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(f"/{self.user.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(User.objects.filter(id=self.user.id).exists())

    def test_admin_delete_user_not_found(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(f"/9999")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
