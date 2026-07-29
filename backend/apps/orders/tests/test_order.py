from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from model_bakery import baker
from rest_framework import status
from rest_framework.test import APIClient

from apps.orders.models import Item, Order, OrderItem

User = get_user_model()

ORDERS_URL = "/api/v1/orders/orders/"


class OrderViewSetTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = baker.make(User, email="owner@example.com")
        cls.other = baker.make(User, email="other@example.com")
        cls.item = baker.make(Item, name="Solarmodul", price=Decimal("100.00"), on_stock=5)
        cls.order = baker.make(
            Order,
            customer=cls.owner,
            email=cls.owner.email,
            order_number="K39-2026-1001",
        )
        cls.other_order = baker.make(
            Order,
            customer=cls.other,
            email=cls.other.email,
            order_number="K39-2026-1002",
        )
        baker.make(
            OrderItem,
            order=cls.order,
            item=cls.item,
            item_name=cls.item.name,
            unit_price=cls.item.price,
            quantity=2,
        )

    def setUp(self):
        self.client = APIClient()

    def test_list_requires_authentication(self):
        response = self.client.get(ORDERS_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_returns_only_own_orders(self):
        self.client.force_authenticate(user=self.owner)

        response = self.client.get(ORDERS_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["order_number"], self.order.order_number)
        self.assertEqual(len(results[0]["items"]), 1)

    def test_retrieve_own_order(self):
        self.client.force_authenticate(user=self.owner)

        response = self.client.get(f"{ORDERS_URL}{self.order.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.order.id)
        self.assertEqual(response.data["order_number"], "K39-2026-1001")
        self.assertEqual(response.data["email"], self.owner.email)
        self.assertEqual(response.data["items"][0]["quantity"], 2)

    def test_retrieve_foreign_order_not_found(self):
        self.client.force_authenticate(user=self.owner)

        response = self.client.get(f"{ORDERS_URL}{self.other_order.id}/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_not_allowed(self):
        self.client.force_authenticate(user=self.owner)

        response = self.client.post(
            ORDERS_URL,
            {"email": "x@example.com"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
