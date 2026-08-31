from decimal import Decimal
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from model_bakery import baker

from apps.orders.models import Item, Order, OrderStatusHistory
from apps.orders.services.fulfillment import FulfillmentService

User = get_user_model()


class FulfillmentServiceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.customer = baker.make(User, email="buyer@example.com")
        cls.item = baker.make(
            Item, name="Solarmodul", price=Decimal("100.00"), on_stock=5
        )

    def _order(self, *, paid: bool = True) -> Order:
        return baker.make(
            Order,
            customer=self.customer,
            email=self.customer.email,
            order_number=f"K39-TEST-{uuid4().hex[:8]}",
            stripe_session_id=f"cs_{uuid4().hex}",
            payment_status=(
                Order.PaymentStatus.PAID if paid else Order.PaymentStatus.PENDING
            ),
            paid_at=timezone.now() if paid else None,
        )

    def test_rejects_status_change_before_payment(self):
        order = self._order(paid=False)

        with self.assertRaises(ValidationError):
            FulfillmentService.update_status(order, Order.FulfillmentStatus.PROCESSING)

    def test_writes_status_history(self):
        order = self._order()

        FulfillmentService.update_status(order, Order.FulfillmentStatus.PROCESSING)

        history = OrderStatusHistory.objects.get(order=order)
        self.assertEqual(history.status_type, OrderStatusHistory.StatusType.FULFILLMENT)
        self.assertEqual(history.old_value, Order.FulfillmentStatus.PENDING)
        self.assertEqual(history.new_value, Order.FulfillmentStatus.PROCESSING)

    def test_sets_shipped_at_only_on_first_transition(self):
        order = self._order()

        FulfillmentService.update_status(
            order,
            Order.FulfillmentStatus.SHIPPED,
            tracking_number="003404",
            carrier="DHL",
        )
        order.refresh_from_db()
        first_shipped_at = order.shipped_at
        self.assertIsNotNone(first_shipped_at)

        FulfillmentService.update_status(
            order,
            Order.FulfillmentStatus.SHIPPED,
            tracking_number="003405",
        )
        order.refresh_from_db()
        self.assertEqual(order.shipped_at, first_shipped_at)
        self.assertEqual(order.tracking_number, "003405")

    def test_sets_delivered_at_only_on_first_transition(self):
        order = self._order()
        FulfillmentService.update_status(order, Order.FulfillmentStatus.SHIPPED)

        FulfillmentService.update_status(order, Order.FulfillmentStatus.DELIVERED)
        order.refresh_from_db()
        first_delivered_at = order.delivered_at
        self.assertIsNotNone(first_delivered_at)

        FulfillmentService.update_status(order, Order.FulfillmentStatus.DELIVERED)
        order.refresh_from_db()
        self.assertEqual(order.delivered_at, first_delivered_at)
