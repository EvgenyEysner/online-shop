from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from model_bakery import baker
from rest_framework import status
from rest_framework.test import APIClient

from apps.orders.models import Invoice, Order, ReturnRequest
from apps.orders.services.notifications import NotificationService

User = get_user_model()

NOTIFICATIONS_URL = "/api/v1/orders/notifications/"
MARK_SEEN_URL = "/api/v1/accounts/user/mark-notifications-seen/"


class NotificationServiceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = baker.make(User, email="buyer@example.com")
        cls.other = baker.make(User, email="other@example.com")
        now = timezone.now()
        cls.order = baker.make(
            Order,
            customer=cls.user,
            email=cls.user.email,
            order_number="K39-2026-7701",
            stripe_session_id="cs_notify_7701",
            payment_status=Order.PaymentStatus.PAID,
            paid_at=now - timedelta(hours=3),
            shipped_at=now - timedelta(hours=2),
            delivered_at=now - timedelta(hours=1),
        )
        baker.make(
            Invoice,
            order=cls.order,
            document_type=Invoice.DocumentType.INVOICE,
            invoice_number="RE-2026-7701",
            service_date=now.date(),
            buyer_name="Max Mustermann",
            buyer_street="Musterstraße 1",
            buyer_zip="39104",
            buyer_city="Magdeburg",
            buyer_country="Deutschland",
            net_amount=Decimal("100.00"),
            tax_rate=Decimal("0.190"),
            tax_amount=Decimal("19.00"),
            total_amount=Decimal("119.00"),
        )
        baker.make(
            ReturnRequest,
            order=cls.order,
            status=ReturnRequest.Status.APPROVED,
            reason="Widerruf",
            decided_at=now,
        )
        baker.make(
            Order,
            customer=cls.other,
            email=cls.other.email,
            order_number="K39-2026-7702",
            stripe_session_id="cs_notify_7702",
        )

    def test_events_are_newest_first_and_own_orders_only(self):
        events = NotificationService.get_recent_events(self.user)

        kinds = [event.kind for event in events]
        self.assertIn("order_created", kinds)
        self.assertIn("order_paid", kinds)
        self.assertIn("order_shipped", kinds)
        self.assertIn("order_delivered", kinds)
        self.assertIn("invoice_issued", kinds)
        self.assertIn("return_status_changed", kinds)
        self.assertTrue(all(event.order_number == "K39-2026-7701" for event in events))
        occurred = [event.occurred_at for event in events]
        self.assertEqual(occurred, sorted(occurred, reverse=True))


class NotificationApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = baker.make(User, email="buyer@example.com")
        baker.make(
            Order,
            customer=cls.user,
            email=cls.user.email,
            order_number="K39-2026-7703",
            stripe_session_id="cs_notify_7703",
            payment_status=Order.PaymentStatus.PAID,
            paid_at=timezone.now(),
        )

    def setUp(self):
        self.client = APIClient()

    def test_requires_authentication(self):
        response = self.client.get(NOTIFICATIONS_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unread_then_mark_seen(self):
        self.client.force_authenticate(user=self.user)

        first = self.client.get(NOTIFICATIONS_URL)
        self.assertEqual(first.status_code, status.HTTP_200_OK)
        self.assertGreater(first.data["unread_count"], 0)
        self.assertFalse(first.data["results"][0]["read"])

        seen = self.client.post(MARK_SEEN_URL)
        self.assertEqual(seen.status_code, status.HTTP_204_NO_CONTENT)

        second = self.client.get(NOTIFICATIONS_URL)
        self.assertEqual(second.data["unread_count"], 0)
        self.assertTrue(all(row["read"] for row in second.data["results"]))
