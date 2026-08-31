from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.utils import timezone
from model_bakery import baker
from rest_framework import status
from rest_framework.test import APIClient

from apps.orders.models import Invoice, Item, Order, OrderItem, ReturnRequest
from apps.orders.services.invoice import InvoiceService
from apps.orders.services.returns import ReturnService

User = get_user_model()

RETURNS_URL = "/api/v1/orders/return-requests/"
FAKE_PDF = b"%PDF-1.4 fake"


class ReturnServiceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.customer = baker.make(User, email="buyer@example.com")
        cls.item = baker.make(
            Item, name="Solarmodul", price=Decimal("100.00"), on_stock=5
        )

    def _order(self, *, paid: bool = True, delivered_at=None) -> Order:
        order = baker.make(
            Order,
            customer=self.customer,
            email=self.customer.email,
            order_number=f"K39-TEST-{uuid4().hex[:8]}",
            stripe_session_id=f"cs_{uuid4().hex}",
            payment_status=(
                Order.PaymentStatus.PAID if paid else Order.PaymentStatus.PENDING
            ),
            paid_at=timezone.now() if paid else None,
            delivered_at=delivered_at,
            subtotal=Decimal("200.00"),
            tax_amount=Decimal("38.00"),
            total=Decimal("238.00"),
        )
        baker.make(
            OrderItem,
            order=order,
            item=self.item,
            item_name=self.item.name,
            unit_price=Decimal("100.00"),
            quantity=2,
        )
        return order

    def test_can_request_return_requires_paid_order(self):
        order = self._order(paid=False)
        self.assertFalse(ReturnService.can_request_return(order))

    def test_can_request_return_allows_missing_delivered_at(self):
        order = self._order(paid=True, delivered_at=None)
        self.assertTrue(ReturnService.can_request_return(order))

    def test_can_request_return_blocks_after_window(self):
        order = self._order(paid=True, delivered_at=timezone.now() - timedelta(days=15))
        self.assertFalse(ReturnService.can_request_return(order))

    def test_can_request_return_allows_within_window(self):
        order = self._order(paid=True, delivered_at=timezone.now() - timedelta(days=3))
        self.assertTrue(ReturnService.can_request_return(order))

    def test_create_request_rejects_quantity_above_ordered(self):
        order = self._order()
        order_item = order.items.get()

        with self.assertRaises(ValidationError):
            ReturnService.create_request(
                order,
                items=[{"order_item": order_item, "quantity": 3}],
                reason="zu groß",
            )

    def test_approve_and_reject_only_from_requested(self):
        order = self._order()
        request = ReturnService.create_request(
            order,
            items=[{"order_item": order.items.get(), "quantity": 1}],
            reason="Widerruf",
        )

        ReturnService.approve(request, actor=self.customer)
        request.refresh_from_db()
        self.assertEqual(request.status, ReturnRequest.Status.APPROVED)
        self.assertIsNotNone(request.decided_at)

        with self.assertRaises(ValidationError):
            ReturnService.reject(request, actor=self.customer, note="zu spät")

    def test_complete_return_restocks_and_is_idempotent(self):
        order = self._order()
        request = ReturnService.create_request(
            order,
            items=[{"order_item": order.items.get(), "quantity": 1}],
            reason="Widerruf",
        )
        ReturnService.approve(request, actor=self.customer)

        with (
            patch.object(InvoiceService, "_render_pdf", return_value=FAKE_PDF),
            patch("apps.orders.services.returns.stripe.Refund.create") as refund,
            patch("apps.orders.services.credit_note.send_invoice_email") as send_email,
        ):
            InvoiceService.ensure_invoice_for_order(order)
            result = ReturnService.complete_return(request, actor=self.customer)
            first_refunded_at = result.refunded_at
            self.assertEqual(result.status, ReturnRequest.Status.REFUNDED)
            request.status = ReturnRequest.Status.APPROVED
            request.save(update_fields=["status"])
            second = ReturnService.complete_return(request, actor=self.customer)

        self.assertEqual(second.refunded_at, first_refunded_at)
        self.assertEqual(
            order.invoices.filter(
                document_type=Invoice.DocumentType.CREDIT_NOTE
            ).count(),
            1,
        )
        self.item.refresh_from_db()
        self.assertEqual(self.item.on_stock, 6)
        refund.assert_not_called()
        send_email.delay.assert_called_once()


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
class ReturnRequestViewSetTests(TestCase):
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
            order_number="K39-TEST-ret1",
            stripe_session_id="cs_return_owner",
            payment_status=Order.PaymentStatus.PAID,
            paid_at=timezone.now(),
        )
        cls.order_item = baker.make(
            OrderItem,
            order=cls.order,
            item=cls.item,
            item_name=cls.item.name,
            unit_price=cls.item.price,
            quantity=2,
        )
        cls.other_order = baker.make(
            Order,
            customer=cls.other,
            email=cls.other.email,
            order_number="K39-TEST-ret2",
            stripe_session_id="cs_return_other",
            payment_status=Order.PaymentStatus.PAID,
            paid_at=timezone.now(),
        )
        cls.other_item = baker.make(
            OrderItem,
            order=cls.other_order,
            item=cls.item,
            item_name=cls.item.name,
            unit_price=cls.item.price,
            quantity=1,
        )

    def setUp(self):
        self.client = APIClient()

    def test_create_rejects_foreign_order(self):
        self.client.force_authenticate(user=self.owner)

        response = self.client.post(
            RETURNS_URL,
            {
                "order": self.other_order.id,
                "reason": "Widerruf",
                "items": [
                    {"order_item": self.other_item.id, "quantity": 1},
                ],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("order", response.data)

    def test_create_rejects_foreign_order_item(self):
        self.client.force_authenticate(user=self.owner)

        response = self.client.post(
            RETURNS_URL,
            {
                "order": self.order.id,
                "reason": "Widerruf",
                "items": [
                    {"order_item": self.other_item.id, "quantity": 1},
                ],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("items", response.data)

    def test_create_own_return_and_list_only_own(self):
        self.client.force_authenticate(user=self.owner)

        created = self.client.post(
            RETURNS_URL,
            {
                "order": self.order.id,
                "reason": "Widerruf",
                "items": [{"order_item": self.order_item.id, "quantity": 1}],
            },
            format="json",
        )
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)

        baker.make(ReturnRequest, order=self.other_order, reason="fremd")

        listed = self.client.get(RETURNS_URL)
        self.assertEqual(listed.status_code, status.HTTP_200_OK)
        self.assertEqual(len(listed.data["results"]), 1)
        self.assertEqual(listed.data["results"][0]["id"], created.data["id"])
