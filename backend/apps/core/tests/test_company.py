from django.conf import settings
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

COMPANY_URL = "/api/v1/core/company/"


class CompanyInfoViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_is_public_and_returns_company_settings(self):
        response = self.client.get(COMPANY_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], settings.COMPANY_NAME)
        self.assertEqual(response.data["street"], settings.COMPANY_STREET)
        self.assertEqual(response.data["zip"], settings.COMPANY_ZIP)
        self.assertEqual(response.data["city"], settings.COMPANY_CITY)
        self.assertEqual(response.data["email"], settings.COMPANY_EMAIL)
        self.assertEqual(response.data["tax_id"], settings.COMPANY_TAX_ID)
