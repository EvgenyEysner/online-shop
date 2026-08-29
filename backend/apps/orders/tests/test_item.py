from decimal import Decimal

from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from apps.orders.models import Category, Item

ITEMS_URL = "/api/v1/orders/items/"


class ItemsViewSetTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.solar = Category.objects.create(
            name="Solarmodule",
            slug="solarmodule",
            sublabel="Photovoltaik",
            image_url="https://example.com/solar.jpg",
        )
        cls.inverter = Category.objects.create(
            name="Wechselrichter",
            slug="wechselrichter",
        )
        cls.item_solar = Item.objects.create(
            name="Solarmodul",
            description="400W Modul",
            image_url="https://example.com/solarmodul.jpg",
            category=cls.solar,
            price=Decimal("100.00"),
            on_stock=5,
        )
        cls.item_inverter = Item.objects.create(
            name="Wechselrichter",
            image_url="https://example.com/wechselrichter.jpg",
            category=cls.inverter,
            price=Decimal("200.00"),
            on_stock=3,
        )
        cls.item_out_of_stock = Item.objects.create(
            name="Kabel",
            category=cls.solar,
            price=Decimal("10.00"),
            on_stock=0,
        )

    def setUp(self):
        self.client = APIClient()

    def test_list_returns_in_stock_items_ordered_by_name(self):
        response = self.client.get(ITEMS_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        self.assertEqual(len(results), 2)
        self.assertEqual(
            [item["name"] for item in results],
            ["Solarmodul", "Wechselrichter"],
        )

    def test_list_excludes_out_of_stock_items(self):
        response = self.client.get(ITEMS_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [item["name"] for item in response.data["results"]]
        self.assertNotIn(self.item_out_of_stock.name, names)

    def test_list_returns_expected_fields(self):
        response = self.client.get(ITEMS_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        item = next(
            entry
            for entry in response.data["results"]
            if entry["name"] == self.item_solar.name
        )
        self.assertEqual(item["id"], self.item_solar.id)
        self.assertEqual(item["name"], "Solarmodul")
        self.assertEqual(item["description"], "400W Modul")
        self.assertEqual(item["image"], "https://example.com/solarmodul.jpg")
        self.assertEqual(item["manufacturer_number"], "")
        self.assertEqual(item["category"], "solarmodule")
        self.assertEqual(item["price"], "100.00")
        self.assertIsNone(item["original_price"])
        self.assertEqual(item["unit"], Item.UnitChoices.PIECES)
        self.assertEqual(item["watt"], "")
        self.assertEqual(item["badge"], "")
        self.assertEqual(str(item["rating"]), "0.0")
        self.assertEqual(item["reviews"], 0)
        self.assertEqual(item["specs"], [])
        self.assertEqual(item["on_stock"], 5)
        self.assertEqual(item["min_stock"], 1)
        self.assertIsNone(item["ean"])
        self.assertEqual(Decimal(str(item["tax"])), Decimal("19.00"))

    def test_list_allows_anonymous_access(self):
        response = self.client.get(ITEMS_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_returns_empty_results_when_no_in_stock_items(self):
        Item.objects.all().update(on_stock=0)

        response = self.client.get(ITEMS_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)
        self.assertEqual(response.data["results"], [])

    def test_retrieve_returns_item(self):
        response = self.client.get(f"{ITEMS_URL}{self.item_solar.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.item_solar.id)
        self.assertEqual(response.data["name"], "Solarmodul")
        self.assertEqual(response.data["category"], "solarmodule")

    def test_create_not_allowed(self):
        response = self.client.post(
            ITEMS_URL,
            {
                "name": "Neues Kabel",
                "price": "15.00",
                "on_stock": 1,
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertFalse(Item.objects.filter(name="Neues Kabel").exists())


class ItemTaxPropertyTests(TestCase):

    def test_tax_uses_default_tax_rate(self):
        item = Item.objects.create(name="Kabel", price=Decimal("100.00"), on_stock=1)

        self.assertEqual(item.tax, Decimal("19.00"))

    @override_settings(TAX_RATE=Decimal("0.07"))
    def test_tax_reflects_overridden_tax_rate(self):
        item = Item.objects.create(name="Kabel", price=Decimal("100.00"), on_stock=1)

        self.assertEqual(item.tax, Decimal("7.00"))

    @override_settings(TAX_RATE=Decimal("0"))
    def test_tax_is_zero_when_tax_rate_is_zero(self):
        item = Item.objects.create(name="Kabel", price=Decimal("100.00"), on_stock=1)

        self.assertEqual(item.tax, Decimal("0.00"))
