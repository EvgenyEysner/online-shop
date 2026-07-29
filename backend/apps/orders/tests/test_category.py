from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.orders.models import Category

CATEGORIES_URL = "/api/v1/orders/categories/"


class CategoryViewSetTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.solar = Category.objects.create(
            name="Solarmodule",
            slug="solarmodule",
            sublabel="Photovoltaik",
            image_url="https://example.com/solar.jpg",
        )
        cls.storage = Category.objects.create(
            name="Speicher",
            slug="speicher",
            sublabel="Batteriespeicher",
            image_url="https://example.com/storage.jpg",
        )
        cls.inverter = Category.objects.create(
            name="Wechselrichter",
            slug="wechselrichter",
        )

    def setUp(self):
        self.client = APIClient()

    def test_list_returns_all_categories_ordered_by_name(self):
        response = self.client.get(CATEGORIES_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        self.assertEqual(
            [category["name"] for category in response.data],
            ["Solarmodule", "Speicher", "Wechselrichter"],
        )

    def test_list_returns_expected_fields(self):
        response = self.client.get(CATEGORIES_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        category = next(item for item in response.data if item["slug"] == "solarmodule")
        self.assertEqual(
            category,
            {
                "id": self.solar.id,
                "name": "Solarmodule",
                "slug": "solarmodule",
                "sublabel": "Photovoltaik",
                "image_url": "https://example.com/solar.jpg",
            },
        )

    def test_list_allows_anonymous_access(self):
        response = self.client.get(CATEGORIES_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_returns_empty_list_when_no_categories(self):
        Category.objects.all().delete()

        response = self.client.get(CATEGORIES_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_create_not_allowed(self):
        response = self.client.post(
            CATEGORIES_URL,
            {
                "name": "Kabel",
                "slug": "kabel",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertFalse(Category.objects.filter(slug="kabel").exists())
