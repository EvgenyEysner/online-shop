from apps.accounts.services.customer_numbers import (
    CUSTOMER_NUMBER_START,
    allocate_customer_number,
)
from django.contrib.auth import get_user_model
from django.test import TestCase
from apps.accounts.global_identifier import GlobalIdentifier
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


class GlobalIdentifierTests(TestCase):
    def test_next_returns_default_on_first_call(self):
        value = GlobalIdentifier.next("test_key", default=200000)
        self.assertEqual(value, 200000)

    def test_next_increments_on_subsequent_calls(self):
        first = GlobalIdentifier.next("increment_key", default=10)
        second = GlobalIdentifier.next("increment_key")
        self.assertEqual(first, 10)
        self.assertEqual(second, 11)

    def test_next_n_returns_range(self):
        values = list(GlobalIdentifier.next_n("batch_key", count=3, default=100))
        self.assertEqual(values, [100, 101, 102])


class CustomerNumberServiceTests(TestCase):
    def test_allocate_first_customer_number(self):
        number = allocate_customer_number()
        self.assertEqual(number, f"K39-{CUSTOMER_NUMBER_START}")

    def test_allocate_increments_sequence(self):
        first = allocate_customer_number()
        second = allocate_customer_number()
        self.assertEqual(first, f"K39-{CUSTOMER_NUMBER_START}")
        self.assertEqual(second, f"K39-{CUSTOMER_NUMBER_START + 1}")


class RegisterViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_sign_up_assigns_customer_number_and_tokens(self):
        response = self.client.post(
            "/api/v1/sign-up/",
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
            "/api/v1/sign-up/",
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

    def test_customer_number_not_accepted_from_client(self):
        response = self.client.post(
            "/api/v1/sign-up/",
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
