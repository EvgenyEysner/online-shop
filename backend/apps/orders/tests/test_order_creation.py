from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from model_bakery import baker

from apps.orders.exceptions import InsufficientStockError
from apps.orders.models import Item, Order, OrderItem
from apps.orders.services.order_creation import OrderCreationService
from apps.orders.services.pricing import PricingService

User = get_user_model()


def payload_for(*, item: Item, quantity: int = 1, **overrides) -> dict:
    data = {
        "email": "buyer@example.com",
        "phone": "+49123456789",
        "note": "Bitte klingeln",
        "payment_method": Order.PaymentMethod.CARD,
        "items": [{"item": item.id, "quantity": quantity}],
        "shipping": {
            "salutation": "Herr",
            "first_name": "Max",
            "last_name": "Mustermann",
            "company": "",
            "street": "Musterstraße",
            "street_no": "1",
            "zip": "10115",
            "city": "Berlin",
            "country": "Deutschland",
        },
        "billing_same_as_shipping": True,
    }
    data.update(overrides)
    return data


class OrderCreationServiceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.item = baker.make(
            Item,
            name="Solarmodul",
            price=Decimal("100.00"),
            on_stock=5,
        )
        cls.customer = baker.make(User, email="customer@example.com")

    def test_create_from_payload_creates_order_items_and_reserves_stock(self):
        expected = PricingService.calculate_totals(
            [{"item": self.item, "quantity": 2}]
        )

        order = OrderCreationService.create_from_payload(
            payload=payload_for(item=self.item, quantity=2),
            stripe_session_id="cs_test_create",
            payment_status=Order.PaymentStatus.PAID,
        )

        self.item.refresh_from_db()
        self.assertEqual(self.item.on_stock, 3)
        self.assertTrue(order.order_number.startswith(f"{settings.SHOP_NUMBER_PREFIX}-"))
        self.assertEqual(order.email, "buyer@example.com")
        self.assertEqual(order.payment_status, Order.PaymentStatus.PAID)
        self.assertEqual(order.stripe_session_id, "cs_test_create")
        self.assertEqual(order.shipping_first_name, "Max")
        self.assertEqual(order.subtotal, expected["subtotal"])
        self.assertEqual(order.tax_amount, expected["tax_amount"])
        self.assertEqual(order.shipping_cost, expected["shipping_cost"])
        self.assertEqual(order.total, expected["total"])
        self.assertEqual(order.items.count(), 1)

        order_item = order.items.get()
        self.assertEqual(order_item.item_id, self.item.id)
        self.assertEqual(order_item.item_name, "Solarmodul")
        self.assertEqual(order_item.unit_price, Decimal("100.00"))
        self.assertEqual(order_item.quantity, 2)

    def test_create_from_payload_assigns_customer(self):
        order = OrderCreationService.create_from_payload(
            payload=payload_for(item=self.item),
            stripe_session_id="cs_test_customer",
            customer=self.customer,
        )

        self.assertEqual(order.customer_id, self.customer.id)

    def test_create_from_payload_is_idempotent_for_same_session(self):
        first = OrderCreationService.create_from_payload(
            payload=payload_for(item=self.item, quantity=1),
            stripe_session_id="cs_test_idempotent",
            payment_status=Order.PaymentStatus.PENDING,
        )
        self.item.refresh_from_db()
        stock_after_first = self.item.on_stock

        second = OrderCreationService.create_from_payload(
            payload=payload_for(item=self.item, quantity=1),
            stripe_session_id="cs_test_idempotent",
            payment_status=Order.PaymentStatus.PENDING,
        )

        self.item.refresh_from_db()
        self.assertEqual(first.id, second.id)
        self.assertEqual(Order.objects.filter(stripe_session_id="cs_test_idempotent").count(), 1)
        self.assertEqual(self.item.on_stock, stock_after_first)
        self.assertEqual(OrderItem.objects.filter(order=first).count(), 1)

    def test_create_from_payload_upgrades_pending_to_paid(self):
        OrderCreationService.create_from_payload(
            payload=payload_for(item=self.item),
            stripe_session_id="cs_test_upgrade",
            payment_status=Order.PaymentStatus.PENDING,
        )

        order = OrderCreationService.create_from_payload(
            payload=payload_for(item=self.item),
            stripe_session_id="cs_test_upgrade",
            stripe_payment_intent_id="pi_test_123",
            payment_status=Order.PaymentStatus.PAID,
        )

        self.assertEqual(order.payment_status, Order.PaymentStatus.PAID)
        self.assertEqual(order.stripe_payment_intent_id, "pi_test_123")

    def test_create_from_payload_raises_on_insufficient_stock(self):
        with self.assertRaises(InsufficientStockError):
            OrderCreationService.create_from_payload(
                payload=payload_for(item=self.item, quantity=99),
                stripe_session_id="cs_test_stock",
            )

        self.assertFalse(Order.objects.filter(stripe_session_id="cs_test_stock").exists())
        self.item.refresh_from_db()
        self.assertEqual(self.item.on_stock, 5)

    def test_restock_order_restores_stock(self):
        order = OrderCreationService.create_from_payload(
            payload=payload_for(item=self.item, quantity=2),
            stripe_session_id="cs_test_restock",
            payment_status=Order.PaymentStatus.PENDING,
        )
        self.item.refresh_from_db()
        self.assertEqual(self.item.on_stock, 3)

        OrderCreationService.restock_order(order)

        self.item.refresh_from_db()
        self.assertEqual(self.item.on_stock, 5)

    def test_restock_order_noop_without_linked_items(self):
        order = baker.make(
            Order,
            order_number="K39-2026-9001",
            stripe_session_id="cs_test_restock_empty",
            email="empty@example.com",
        )

        OrderCreationService.restock_order(order)

        self.item.refresh_from_db()
        self.assertEqual(self.item.on_stock, 5)
