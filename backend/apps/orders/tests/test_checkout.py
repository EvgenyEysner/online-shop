from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from model_bakery import baker
from rest_framework import status
from rest_framework.test import APIClient

from apps.orders.models import Item, Order

CHECKOUT_SESSION_URL = "/api/v1/orders/checkout/create-session/"
CHECKOUT_CONFIRM_URL = "/api/v1/orders/checkout/confirm/"


def checkout_payload(*, item: Item, quantity: int = 1, **overrides) -> dict:
    payload = {
        "email": "buyer@example.com",
        "phone": "+49123456789",
        "payment_method": Order.PaymentMethod.CARD,
        "items": [{"item": item.id, "quantity": quantity}],
        "shipping": {
            "first_name": "Max",
            "last_name": "Mustermann",
            "street": "Musterstraße",
            "street_no": "1",
            "zip": "10115",
            "city": "Berlin",
            "country": "Deutschland",
        },
        "billing_same_as_shipping": True,
    }
    payload.update(overrides)
    return payload


class CheckoutViewSetTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.item = baker.make(
            Item,
            name="Solarmodul",
            price=Decimal("100.00"),
            on_stock=5,
        )

    def setUp(self):
        self.client = APIClient()

    @patch("apps.orders.serializers.OrderService.create_checkout_session")
    def test_create_session_returns_session_payload(self, mock_create):
        mock_create.return_value = {
            "session_id": "cs_test_123",
            "url": "https://checkout.stripe.com/c/pay/cs_test_123",
            "draft_id": "11111111-1111-1111-1111-111111111111",
            "public_key": "pk_test_x",
        }

        response = self.client.post(
            CHECKOUT_SESSION_URL,
            checkout_payload(item=self.item),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["session_id"], "cs_test_123")
        self.assertEqual(response.data["url"], mock_create.return_value["url"])
        mock_create.assert_called_once()

    def test_create_session_rejects_empty_cart(self):
        payload = checkout_payload(item=self.item)
        payload["items"] = []

        response = self.client.post(CHECKOUT_SESSION_URL, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("items", response.data)

    def test_create_session_requires_billing_when_different(self):
        payload = checkout_payload(
            item=self.item,
            billing_same_as_shipping=False,
        )

        response = self.client.post(CHECKOUT_SESSION_URL, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("billing", response.data)

    def test_create_session_rejects_quantity_above_stock(self):
        payload = checkout_payload(item=self.item, quantity=99)

        response = self.client.post(CHECKOUT_SESSION_URL, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_confirm_requires_session_id(self):
        response = self.client.get(CHECKOUT_CONFIRM_URL)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "session_id fehlt.")

    @patch("apps.orders.views.OrderService.confirm_session")
    def test_confirm_returns_order(self, mock_confirm):
        order = baker.make(
            Order,
            order_number="K39-2026-2001",
            email="buyer@example.com",
            stripe_session_id="cs_test_confirm",
            payment_status=Order.PaymentStatus.PAID,
        )
        mock_confirm.return_value = order

        response = self.client.get(
            CHECKOUT_CONFIRM_URL,
            {"session_id": "cs_test_confirm"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["order_number"], "K39-2026-2001")
        mock_confirm.assert_called_once_with("cs_test_confirm")

    @patch("apps.orders.views.OrderService.confirm_session")
    def test_confirm_returns_400_on_value_error(self, mock_confirm):
        mock_confirm.side_effect = ValueError("Zahlung noch nicht abgeschlossen.")

        response = self.client.get(
            CHECKOUT_CONFIRM_URL,
            {"session_id": "cs_test_pending"},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "Zahlung noch nicht abgeschlossen.")
