from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core import mail
from django.test import TestCase, override_settings
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from model_bakery import baker
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()

REQUEST_URL = "/api/v1/accounts/password-reset/"
CONFIRM_URL = "/api/v1/accounts/password-reset/confirm/"
OLD_PASSWORD = "SecurePass123!"
NEW_PASSWORD = "NewSecurePass123!"


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
class PasswordResetViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = baker.make(
            User,
            email="reset@example.com",
            first_name="Max",
            last_name="Mustermann",
        )
        self.user.set_password(OLD_PASSWORD)
        self.user.save(update_fields=["password"])

    def test_request_returns_200_for_existing_and_unknown_email(self):
        existing = self.client.post(
            REQUEST_URL, {"email": self.user.email}, format="json"
        )
        unknown = self.client.post(
            REQUEST_URL, {"email": "nobody@example.com"}, format="json"
        )

        self.assertEqual(existing.status_code, status.HTTP_200_OK)
        self.assertEqual(unknown.status_code, status.HTTP_200_OK)
        self.assertEqual(existing.data, unknown.data)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("reset-password", mail.outbox[0].body)

    def test_confirm_sets_password_and_invalidates_token(self):
        token = PasswordResetTokenGenerator().make_token(self.user)
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))

        response = self.client.post(
            CONFIRM_URL,
            {
                "uid": uid,
                "token": token,
                "password": NEW_PASSWORD,
                "password_confirm": NEW_PASSWORD,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(NEW_PASSWORD))

        reused = self.client.post(
            CONFIRM_URL,
            {
                "uid": uid,
                "token": token,
                "password": "AnotherPass123!",
                "password_confirm": "AnotherPass123!",
            },
            format="json",
        )
        self.assertEqual(reused.status_code, status.HTTP_400_BAD_REQUEST)

    def test_confirm_rejects_invalid_token(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))

        response = self.client.post(
            CONFIRM_URL,
            {
                "uid": uid,
                "token": "not-a-valid-token",
                "password": NEW_PASSWORD,
                "password_confirm": NEW_PASSWORD,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(OLD_PASSWORD))
