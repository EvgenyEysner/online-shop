from decimal import Decimal
from unittest.mock import patch
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone
from model_bakery import baker

from apps.orders.models import Item, Order
from apps.orders.services.fulfillment import FulfillmentService
from apps.orders.services.invoice import InvoiceService
from apps.orders.services.order_creation import OrderCreationService
from apps.orders.tasks import send_order_confirmation_email
from apps.orders.tests.test_order_creation import payload_for

User = get_user_model()


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
class TransactionalEmailTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.item = baker.make(
            Item, name="Solarmodul", price=Decimal("100.00"), on_stock=10
        )
        cls.customer = baker.make(User, email="customer@example.com")

    def setUp(self):
        patcher = patch.object(
            InvoiceService, "_render_pdf", return_value=b"%PDF-1.4 fake"
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_new_order_sends_confirmation_once(self):
        order = OrderCreationService.create_from_payload(
            payload=payload_for(
                item=self.item,
                payment_method=Order.PaymentMethod.BANK,
            ),
            stripe_session_id="cs_email_new",
            payment_status=Order.PaymentStatus.PENDING,
        )

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(order.order_number, mail.outbox[0].subject)
        self.assertIn("überweisen", mail.outbox[0].body.lower())
        order.refresh_from_db()
        self.assertIsNotNone(order.confirmation_sent_at)

        send_order_confirmation_email(order.pk)
        self.assertEqual(len(mail.outbox), 1)

    def test_update_existing_does_not_send_second_confirmation(self):
        OrderCreationService.create_from_payload(
            payload=payload_for(item=self.item),
            stripe_session_id="cs_email_update",
            payment_status=Order.PaymentStatus.PENDING,
        )
        mail.outbox.clear()

        OrderCreationService.create_from_payload(
            payload=payload_for(item=self.item),
            stripe_session_id="cs_email_update",
            payment_status=Order.PaymentStatus.PAID,
        )

        confirmation_mails = [
            message
            for message in mail.outbox
            if message.subject.startswith("Bestellbestätigung")
        ]
        self.assertEqual(confirmation_mails, [])

    def test_shipping_notification_only_on_first_shipped_transition(self):
        order = baker.make(
            Order,
            customer=self.customer,
            email=self.customer.email,
            payment_status=Order.PaymentStatus.PAID,
            paid_at=timezone.now(),
            order_number=f"K39-TEST-{uuid4().hex[:8]}",
            stripe_session_id=f"cs_{uuid4().hex}",
        )

        FulfillmentService.update_status(order, Order.FulfillmentStatus.SHIPPED)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("versandt", mail.outbox[0].subject.lower())

        FulfillmentService.update_status(
            order,
            Order.FulfillmentStatus.SHIPPED,
            tracking_number="003404",
        )
        self.assertEqual(len(mail.outbox), 1)
