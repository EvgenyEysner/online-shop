from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings
from model_bakery import baker
from rest_framework import status
from rest_framework.test import APIClient

from apps.orders.models import Item, Order, OrderItem

WEBHOOK_URL = "/api/v1/orders/stripe/webhook/"


@override_settings(STRIPE_WEBHOOK_SECRET="whsec_test")
class StripeWebhookViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def _post_webhook(self, *, signature: str = "sig_test"):
        return self.client.post(
            WEBHOOK_URL,
            data=b'{"id":"evt_test"}',
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE=signature,
        )

    @patch("apps.orders.views.stripe.Webhook.construct_event")
    def test_webhook_rejects_invalid_signature(self, mock_construct):
        import stripe

        mock_construct.side_effect = stripe.error.SignatureVerificationError(
            "bad sig", "sig_header"
        )

        response = self._post_webhook()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("apps.orders.views.OrderService.fulfill_stripe_session")
    @patch("apps.orders.views.stripe.Webhook.construct_event")
    def test_webhook_fulfills_completed_session(self, mock_construct, mock_fulfill):
        session = {"id": "cs_test_paid"}
        mock_construct.return_value = {
            "type": "checkout.session.completed",
            "data": {"object": session},
        }

        response = self._post_webhook()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"received": True})
        mock_fulfill.assert_called_once_with(session)

    @patch("apps.orders.views.OrderService.fulfill_stripe_session")
    @patch("apps.orders.views.stripe.Webhook.construct_event")
    def test_webhook_fulfills_async_payment_succeeded(
        self, mock_construct, mock_fulfill
    ):
        session = {"id": "cs_test_async"}
        mock_construct.return_value = {
            "type": "checkout.session.async_payment_succeeded",
            "data": {"object": session},
        }

        response = self._post_webhook()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_fulfill.assert_called_once_with(session)

    @patch("apps.orders.views.OrderCreationService.restock_order")
    @patch("apps.orders.views.stripe.Webhook.construct_event")
    def test_webhook_marks_failed_and_restocks(self, mock_construct, mock_restock):
        item = baker.make(Item, price=Decimal("50.00"), on_stock=1)
        order = baker.make(
            Order,
            order_number="K39-2026-3001",
            stripe_session_id="cs_test_failed",
            payment_status=Order.PaymentStatus.PENDING,
        )
        baker.make(
            OrderItem,
            order=order,
            item=item,
            item_name=item.name,
            unit_price=item.price,
            quantity=1,
        )
        mock_construct.return_value = {
            "type": "checkout.session.async_payment_failed",
            "data": {"object": {"id": "cs_test_failed"}},
        }

        response = self._post_webhook()

        order.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(order.payment_status, Order.PaymentStatus.FAILED)
        mock_restock.assert_called_once()
        self.assertEqual(mock_restock.call_args.args[0].id, order.id)

    @patch("apps.orders.views.OrderCreationService.restock_order")
    @patch("apps.orders.views.OrderService.fulfill_stripe_session")
    @patch("apps.orders.views.stripe.Webhook.construct_event")
    def test_webhook_ignores_unknown_event_types(
        self, mock_construct, mock_fulfill, mock_restock
    ):
        mock_construct.return_value = {
            "type": "payment_intent.created",
            "data": {"object": MagicMock()},
        }

        response = self._post_webhook()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"received": True})
        mock_fulfill.assert_not_called()
        mock_restock.assert_not_called()
