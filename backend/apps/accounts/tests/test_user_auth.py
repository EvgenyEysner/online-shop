from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()

USER_PASSWORD = "SecurePass123!"


class RegisterViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_sign_up_assigns_customer_number_and_tokens(self):
        response = self.client.post(
            "/api/v1/accounts/sign-up/",
            {
                "email": "new@example.com",
                "first_name": "Max",
                "last_name": "Mustermann",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertTrue(response.data["user"]["customer_number"].startswith("K39-"))

        user = User.objects.get(email="new@example.com")
        self.assertEqual(user.customer_number, response.data["user"]["customer_number"])
        self.assertIsNotNone(user.customer_number)

    def test_sign_up_rejects_password_mismatch(self):
        response = self.client.post(
            "/api/v1/accounts/sign-up/",
            {
                "email": "mismatch@example.com",
                "first_name": "Max",
                "last_name": "Mustermann",
                "password": "SecurePass123!",
                "password_confirm": "Different123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_sign_up_rejects_password_without_digit(self):
        response = self.client.post(
            "/api/v1/accounts/sign-up/",
            {
                "email": "weak@example.com",
                "first_name": "Max",
                "last_name": "Mustermann",
                "password": "SecurePass!",
                "password_confirm": "SecurePass!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_sign_up_rejects_password_without_special_character(self):
        response = self.client.post(
            "/api/v1/accounts/sign-up/",
            {
                "email": "weak2@example.com",
                "first_name": "Max",
                "last_name": "Mustermann",
                "password": "SecurePass123",
                "password_confirm": "SecurePass123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_customer_number_not_accepted_from_client(self):
        response = self.client.post(
            "/api/v1/accounts/sign-up/",
            {
                "email": "hacker@example.com",
                "first_name": "Bad",
                "last_name": "Actor",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
                "customer_number": "K39-999999",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email="hacker@example.com")
        self.assertNotEqual(user.customer_number, "K39-999999")
        self.assertTrue(user.customer_number.startswith("K39-"))


class LoginRefreshTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="test@example.com",
            first_name="Test",
            last_name="User",
            password=USER_PASSWORD,
        )

    def setUp(self):
        self.client = APIClient()

    def test_login_refresh(self):
        response = self.client.post(
            "/api/v1/login/",
            {
                "email": self.user.email,
                "password": USER_PASSWORD,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

        refresh_response = self.client.post(
            "/api/v1/login/refresh/",
            {"refresh": response.data["refresh"]},
            format="json",
        )

        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn("access", refresh_response.data)
