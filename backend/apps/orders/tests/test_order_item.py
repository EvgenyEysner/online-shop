from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from model_bakery import baker
from rest_framework import status
from rest_framework.test import APIClient

from apps.orders.models import Item, Order, OrderItem

User = get_user_model()

ORDER_ITEMS_URL = "/api/v1/orders/order-items/"


class OrderItemViewSetTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = baker.make(User, email="owner@example.com")
        cls.other = baker.make(User, email="other@example.com")
        cls.item = baker.make(
            Item, name="Solarmodul", price=Decimal("100.00"), on_stock=5
        )
        cls.order = baker.make(
            Order,
            customer=cls.owner,
            email=cls.owner.email,
            order_number="K39-2026-1101",
        )
        cls.other_order = baker.make(
            Order,
            customer=cls.other,
            email=cls.other.email,
            order_number="K39-2026-1102",
        )
        cls.order_item = baker.make(
            OrderItem,
            order=cls.order,
            item=cls.item,
            item_name=cls.item.name,
            unit_price=cls.item.price,
            quantity=3,
        )
        cls.other_order_item = baker.make(
            OrderItem,
            order=cls.other_order,
            item=cls.item,
            item_name=cls.item.name,
            unit_price=cls.item.price,
            quantity=1,
        )

    def setUp(self):
        self.client = APIClient()

    def test_list_requires_authentication(self):
        response = self.client.get(ORDER_ITEMS_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_returns_only_own_order_items(self):
        self.client.force_authenticate(user=self.owner)

        response = self.client.get(ORDER_ITEMS_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], self.order_item.id)
        self.assertEqual(results[0]["quantity"], 3)
        self.assertEqual(results[0]["line_total"], "300.00")

    def test_retrieve_own_order_item(self):
        self.client.force_authenticate(user=self.owner)

        response = self.client.get(f"{ORDER_ITEMS_URL}{self.order_item.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.order_item.id)
        self.assertEqual(response.data["item"], self.order_item.item.name)
        self.assertEqual(response.data["item_name"], self.order_item.item_name)

    def test_retrieve_foreign_order_item_not_found(self):
        self.client.force_authenticate(user=self.owner)

        response = self.client.get(f"{ORDER_ITEMS_URL}{self.other_order_item.id}/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_not_allowed(self):
        self.client.force_authenticate(user=self.owner)

        response = self.client.post(
            ORDER_ITEMS_URL,
            {"quantity": 1},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
