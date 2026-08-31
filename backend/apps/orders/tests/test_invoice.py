from decimal import Decimal
from unittest.mock import patch
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone
from model_bakery import baker
from rest_framework import status
from rest_framework.test import APIClient

from apps.orders.models import Invoice, Item, Order, OrderItem
from apps.orders.services.credit_note import CreditNoteService
from apps.orders.services.invoice import InvoiceService
from apps.orders.services.order import OrderService

User = get_user_model()

INVOICES_URL = "/api/v1/orders/invoices/"
FAKE_PDF = b"%PDF-1.4 fake invoice"


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
class InvoiceServiceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.customer = baker.make(User, email="buyer@example.com")
        cls.item = baker.make(
            Item, name="Solarmodul", price=Decimal("100.00"), on_stock=5
        )

    def setUp(self):
        patcher = patch.object(InvoiceService, "_render_pdf", return_value=FAKE_PDF)
        patcher.start()
        self.addCleanup(patcher.stop)

    def _paid_order(self, **overrides) -> Order:
        order = baker.make(
            Order,
            customer=self.customer,
            email=self.customer.email,
            order_number=f"K39-TEST-{uuid4().hex[:8]}",
            stripe_session_id=f"cs_{uuid4().hex}",
            payment_status=Order.PaymentStatus.PENDING,
            shipping_first_name="Max",
            shipping_last_name="Mustermann",
            shipping_street="Musterstraße",
            shipping_street_no="1",
            shipping_zip="39104",
            shipping_city="Magdeburg",
            subtotal=Decimal("100.00"),
            tax_amount=Decimal("19.00"),
            total=Decimal("119.00"),
            **overrides,
        )
        baker.make(
            OrderItem,
            order=order,
            item=self.item,
            item_name=self.item.name,
            unit_price=self.item.price,
            quantity=1,
        )
        return order

    def test_mark_as_paid_creates_invoice_with_re_number(self):
        order = self._paid_order()

        OrderService.mark_as_paid(order)
        invoice = order.invoices.get(document_type=Invoice.DocumentType.INVOICE)

        year = timezone.now().year
        self.assertTrue(invoice.invoice_number.startswith(f"RE-{year}-"))
        self.assertEqual(invoice.net_amount, Decimal("100.00"))
        self.assertEqual(invoice.tax_amount, Decimal("19.00"))
        self.assertEqual(invoice.total_amount, Decimal("119.00"))
        self.assertTrue(invoice.pdf_file.name.endswith(".pdf"))

    def test_ensure_invoice_is_idempotent(self):
        order = self._paid_order()
        first = InvoiceService.ensure_invoice_for_order(order)
        second = InvoiceService.ensure_invoice_for_order(order)

        self.assertEqual(first.pk, second.pk)
        self.assertEqual(
            order.invoices.filter(document_type=Invoice.DocumentType.INVOICE).count(),
            1,
        )

    def test_invoice_is_immutable_after_creation(self):
        order = self._paid_order()
        invoice = InvoiceService.ensure_invoice_for_order(order)

        invoice.total_amount = Decimal("1.00")
        with self.assertRaises(ValueError) as ctx:
            invoice.save()
        self.assertIn("unveränderbar", str(ctx.exception))

    def test_invoice_cannot_be_deleted(self):
        order = self._paid_order()
        invoice = InvoiceService.ensure_invoice_for_order(order)

        with self.assertRaises(ValueError) as ctx:
            invoice.delete()
        self.assertIn("nicht gelöscht", str(ctx.exception))

    def test_sent_at_may_be_updated(self):
        order = self._paid_order()
        invoice = InvoiceService.ensure_invoice_for_order(order)

        invoice.sent_at = timezone.now()
        invoice.save(update_fields=["sent_at"])
        invoice.refresh_from_db()
        self.assertIsNotNone(invoice.sent_at)


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
class CreditNoteServiceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.customer = baker.make(User, email="buyer@example.com")
        cls.item = baker.make(
            Item, name="Solarmodul", price=Decimal("100.00"), on_stock=5
        )

    def setUp(self):
        patcher = patch.object(InvoiceService, "_render_pdf", return_value=FAKE_PDF)
        patcher.start()
        self.addCleanup(patcher.stop)

    def _invoice(self) -> Invoice:
        order = baker.make(
            Order,
            customer=self.customer,
            email=self.customer.email,
            order_number=f"K39-TEST-{uuid4().hex[:8]}",
            stripe_session_id=f"cs_{uuid4().hex}",
            payment_status=Order.PaymentStatus.PAID,
            paid_at=timezone.now(),
            shipping_first_name="Max",
            shipping_last_name="Mustermann",
            shipping_street="Musterstraße",
            shipping_zip="39104",
            shipping_city="Magdeburg",
            subtotal=Decimal("100.00"),
            tax_amount=Decimal("19.00"),
            total=Decimal("119.00"),
        )
        baker.make(
            OrderItem,
            order=order,
            item=self.item,
            item_name=self.item.name,
            unit_price=self.item.price,
            quantity=1,
        )
        return InvoiceService.ensure_invoice_for_order(order)

    def test_issue_credit_note_uses_gs_number_and_references_invoice(self):
        invoice = self._invoice()

        credit_note = CreditNoteService.issue_credit_note(
            invoice,
            net_amount=invoice.net_amount,
            tax_amount=invoice.tax_amount,
            total_amount=invoice.total_amount,
            reason="Manueller Storno durch Staff",
        )

        year = timezone.now().year
        self.assertEqual(credit_note.document_type, Invoice.DocumentType.CREDIT_NOTE)
        self.assertTrue(credit_note.invoice_number.startswith(f"GS-{year}-"))
        self.assertEqual(credit_note.credited_invoice_id, invoice.pk)
        self.assertEqual(credit_note.reason, "Manueller Storno durch Staff")
        self.assertEqual(invoice.credit_notes.count(), 1)


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
class InvoiceViewSetTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = baker.make(User, email="owner@example.com")
        cls.other = baker.make(User, email="other@example.com")
        cls.item = baker.make(
            Item, name="Solarmodul", price=Decimal("100.00"), on_stock=5
        )

    def setUp(self):
        self.client = APIClient()
        patcher = patch.object(InvoiceService, "_render_pdf", return_value=FAKE_PDF)
        patcher.start()
        self.addCleanup(patcher.stop)

        order = baker.make(
            Order,
            customer=self.owner,
            email=self.owner.email,
            order_number=f"K39-TEST-{uuid4().hex[:8]}",
            stripe_session_id=f"cs_{uuid4().hex}",
            payment_status=Order.PaymentStatus.PAID,
            paid_at=timezone.now(),
            shipping_first_name="Max",
            shipping_last_name="Mustermann",
            shipping_street="Musterstraße",
            shipping_zip="39104",
            shipping_city="Magdeburg",
            subtotal=Decimal("100.00"),
            tax_amount=Decimal("19.00"),
            total=Decimal("119.00"),
        )
        baker.make(
            OrderItem,
            order=order,
            item=self.item,
            item_name=self.item.name,
            unit_price=self.item.price,
            quantity=1,
        )
        self.invoice = InvoiceService.ensure_invoice_for_order(order)

        other_order = baker.make(
            Order,
            customer=self.other,
            email=self.other.email,
            order_number=f"K39-TEST-{uuid4().hex[:8]}",
            stripe_session_id=f"cs_{uuid4().hex}",
            payment_status=Order.PaymentStatus.PAID,
            paid_at=timezone.now(),
            shipping_first_name="Eva",
            shipping_last_name="Beispiel",
            shipping_street="Andere Straße",
            shipping_zip="10115",
            shipping_city="Berlin",
            subtotal=Decimal("50.00"),
            tax_amount=Decimal("9.50"),
            total=Decimal("59.50"),
        )
        baker.make(
            OrderItem,
            order=other_order,
            item=self.item,
            item_name=self.item.name,
            unit_price=self.item.price,
            quantity=1,
        )
        self.other_invoice = InvoiceService.ensure_invoice_for_order(other_order)

    def test_list_requires_authentication(self):
        response = self.client.get(INVOICES_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_returns_only_own_invoices(self):
        self.client.force_authenticate(user=self.owner)

        response = self.client.get(INVOICES_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        numbers = [row["invoice_number"] for row in response.data["results"]]
        self.assertEqual(numbers, [self.invoice.invoice_number])

    def test_download_own_invoice(self):
        self.client.force_authenticate(user=self.owner)

        response = self.client.get(f"{INVOICES_URL}{self.invoice.id}/download/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "application/pdf")

    def test_download_foreign_invoice_is_not_found(self):
        self.client.force_authenticate(user=self.owner)

        response = self.client.get(f"{INVOICES_URL}{self.other_invoice.id}/download/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
