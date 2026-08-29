from decimal import Decimal
from unittest.mock import MagicMock, patch
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from model_bakery import baker

from apps.orders.exceptions import InsufficientStockError
from apps.orders.models import CheckoutDraft, Item, Order
from apps.orders.services.order import OrderService
from apps.orders.services.stripe_checkout import StripeCheckoutService

User = get_user_model()

SUCCESS_URL = "https://shop.example/checkout?session_id={CHECKOUT_SESSION_ID}"
CANCEL_URL = "https://shop.example/checkout?cancelled=1"


def checkout_payload(*, item: Item, quantity: int = 1, **overrides) -> dict:
    data = {
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
    data.update(overrides)
    return data


def fake_session(*, session_id: str = "cs_test_123") -> MagicMock:
    session = MagicMock()
    session.id = session_id
    session.url = f"https://checkout.stripe.com/c/pay/{session_id}"
    return session


@override_settings(STRIPE_PUBLIC_KEY="pk_test_public")
class OrderServiceCreateCheckoutSessionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.item = baker.make(
            Item,
            name="Solarmodul",
            price=Decimal("100.00"),
            on_stock=5,
        )
        cls.customer = baker.make(User, email="customer@example.com")

    @patch.object(StripeCheckoutService, "create_session")
    def test_card_creates_draft_without_order(self, mock_create_session):
        mock_create_session.return_value = fake_session(session_id="cs_card")

        result = OrderService.create_checkout_session(
            payload=checkout_payload(item=self.item),
            customer=self.customer,
            success_url=SUCCESS_URL,
            cancel_url=CANCEL_URL,
        )

        draft = CheckoutDraft.objects.get(stripe_session_id="cs_card")
        self.assertEqual(result["session_id"], "cs_card")
        self.assertEqual(result["url"], "https://checkout.stripe.com/c/pay/cs_card")
        self.assertEqual(result["draft_id"], str(draft.id))
        self.assertEqual(result["public_key"], "pk_test_public")
        self.assertEqual(draft.payload["customer_id"], self.customer.id)
        self.assertEqual(
            draft.payload["items"],
            [{"item": self.item.id, "quantity": 1}],
        )
        self.assertFalse(Order.objects.filter(stripe_session_id="cs_card").exists())
        self.item.refresh_from_db()
        self.assertEqual(self.item.on_stock, 5)

    @patch.object(StripeCheckoutService, "create_session")
    def test_bank_creates_pending_order_and_reserves_stock(self, mock_create_session):
        mock_create_session.return_value = fake_session(session_id="cs_bank")

        result = OrderService.create_checkout_session(
            payload=checkout_payload(
                item=self.item,
                quantity=2,
                payment_method=Order.PaymentMethod.BANK,
            ),
            customer=self.customer,
            success_url=SUCCESS_URL,
            cancel_url=CANCEL_URL,
        )

        order = Order.objects.get(stripe_session_id="cs_bank")
        self.item.refresh_from_db()
        self.assertEqual(result["session_id"], "cs_bank")
        self.assertEqual(order.payment_status, Order.PaymentStatus.PENDING)
        self.assertEqual(order.customer_id, self.customer.id)
        self.assertEqual(self.item.on_stock, 3)
        self.assertEqual(order.items.count(), 1)

    @patch("apps.orders.services.order.stripe.checkout.Session.expire")
    @patch("apps.orders.services.order.OrderCreationService.create_from_payload")
    @patch.object(StripeCheckoutService, "create_session")
    def test_async_stock_error_expires_session(
        self, mock_create_session, mock_create_order, mock_expire
    ):
        mock_create_session.return_value = fake_session(session_id="cs_expire")
        mock_create_order.side_effect = InsufficientStockError("kein Bestand")

        with self.assertRaises(InsufficientStockError):
            OrderService.create_checkout_session(
                payload=checkout_payload(
                    item=self.item,
                    payment_method=Order.PaymentMethod.INVOICE,
                ),
                success_url=SUCCESS_URL,
                cancel_url=CANCEL_URL,
            )

        mock_expire.assert_called_once_with("cs_expire")
        self.assertFalse(Order.objects.filter(stripe_session_id="cs_expire").exists())

    def test_rejects_quantity_above_stock_before_stripe(self):
        with self.assertRaises(InsufficientStockError):
            OrderService.create_checkout_session(
                payload=checkout_payload(item=self.item, quantity=99),
                success_url=SUCCESS_URL,
                cancel_url=CANCEL_URL,
            )

        self.assertEqual(CheckoutDraft.objects.count(), 0)


class OrderServiceCreateOrderOrRefundTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.item = baker.make(
            Item,
            name="Wechselrichter",
            price=Decimal("200.00"),
            on_stock=2,
        )

    def test_creates_order_on_success(self):
        order = OrderService._create_order_or_refund(
            payload=checkout_payload(item=self.item),
            stripe_session_id="cs_refund_ok",
            stripe_payment_intent_id="pi_ok",
            payment_status=Order.PaymentStatus.PAID,
        )

        self.assertIsNotNone(order)
        self.assertEqual(order.payment_status, Order.PaymentStatus.PAID)
        self.assertEqual(order.stripe_payment_intent_id, "pi_ok")

    @patch("apps.orders.services.order.stripe.Refund.create")
    @patch("apps.orders.services.order.OrderCreationService.create_from_payload")
    def test_paid_stock_error_triggers_refund(self, mock_create, mock_refund):
        mock_create.side_effect = InsufficientStockError("leer")

        result = OrderService._create_order_or_refund(
            payload={},
            stripe_session_id="cs_refund_paid",
            stripe_payment_intent_id="pi_refund",
            payment_status=Order.PaymentStatus.PAID,
        )

        self.assertIsNone(result)
        mock_refund.assert_called_once_with(payment_intent="pi_refund")

    @patch("apps.orders.services.order.stripe.Refund.create")
    @patch("apps.orders.services.order.OrderCreationService.create_from_payload")
    def test_paid_stock_error_logs_critical_error(self, mock_create, mock_refund):
        """
        Der kritische Refund-Fehlerpfad muss über den
        apps -Logger sichtbar sein.
        """
        mock_create.side_effect = InsufficientStockError("leer")

        with self.assertLogs("apps.orders.services.order", level="ERROR") as logs:
            result = OrderService._create_order_or_refund(
                payload={},
                stripe_session_id="cs_refund_log",
                stripe_payment_intent_id="pi_log",
                payment_status=Order.PaymentStatus.PAID,
            )

        self.assertIsNone(result)
        self.assertEqual(len(logs.output), 1)
        self.assertIn("cs_refund_log", logs.output[0])
        self.assertIn("paid", logs.output[0])

    @patch("apps.orders.services.order.stripe.Refund.create")
    @patch("apps.orders.services.order.OrderCreationService.create_from_payload")
    def test_pending_stock_error_skips_refund(self, mock_create, mock_refund):
        mock_create.side_effect = InsufficientStockError("leer")

        result = OrderService._create_order_or_refund(
            payload={},
            stripe_session_id="cs_refund_pending",
            stripe_payment_intent_id="pi_pending",
            payment_status=Order.PaymentStatus.PENDING,
        )

        self.assertIsNone(result)
        mock_refund.assert_not_called()


class OrderServiceFulfillStripeSessionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.item = baker.make(
            Item,
            name="Speicher",
            price=Decimal("50.00"),
            on_stock=4,
        )
        cls.customer = baker.make(User, email="fulfill@example.com")

    def _create_draft(self, *, session_id: str, customer_id=None) -> CheckoutDraft:
        payload = checkout_payload(item=self.item, quantity=1)
        payload["items"] = [{"item": self.item.id, "quantity": 1}]
        payload["customer_id"] = customer_id
        return CheckoutDraft.objects.create(
            id=uuid4(),
            payload=payload,
            stripe_session_id=session_id,
        )

    def test_paid_session_creates_paid_order_from_draft(self):
        draft = self._create_draft(session_id="cs_fulfill_paid")
        session = {
            "id": "cs_fulfill_paid",
            "payment_status": "paid",
            "status": "complete",
            "payment_intent": "pi_fulfill",
            "metadata": {
                "draft_id": str(draft.id),
                "payment_method": Order.PaymentMethod.CARD,
            },
        }

        order = OrderService.fulfill_stripe_session(session)

        self.assertIsNotNone(order)
        self.assertEqual(order.payment_status, Order.PaymentStatus.PAID)
        self.assertEqual(order.stripe_payment_intent_id, "pi_fulfill")
        self.item.refresh_from_db()
        self.assertEqual(self.item.on_stock, 3)

    def test_async_unpaid_session_creates_pending_order(self):
        draft = self._create_draft(session_id="cs_fulfill_async")
        session = {
            "id": "cs_fulfill_async",
            "payment_status": "unpaid",
            "status": "open",
            "payment_intent": None,
            "metadata": {
                "draft_id": str(draft.id),
                "payment_method": Order.PaymentMethod.BANK,
            },
        }

        order = OrderService.fulfill_stripe_session(session)

        self.assertIsNotNone(order)
        self.assertEqual(order.payment_status, Order.PaymentStatus.PENDING)

    def test_existing_order_upgrades_to_paid(self):
        order = baker.make(
            Order,
            order_number="K39-2026-8001",
            email="buyer@example.com",
            stripe_session_id="cs_fulfill_upgrade",
            payment_status=Order.PaymentStatus.PENDING,
        )
        session = {
            "id": "cs_fulfill_upgrade",
            "payment_status": "paid",
            "status": "complete",
            "payment_intent": "pi_upgrade",
            "metadata": {},
        }

        result = OrderService.fulfill_stripe_session(session)

        order.refresh_from_db()
        self.assertEqual(result.id, order.id)
        self.assertEqual(order.payment_status, Order.PaymentStatus.PAID)
        self.assertEqual(order.stripe_payment_intent_id, "pi_upgrade")

    def test_existing_unpaid_order_returned_unchanged(self):
        order = baker.make(
            Order,
            order_number="K39-2026-8002",
            email="buyer@example.com",
            stripe_session_id="cs_fulfill_keep",
            payment_status=Order.PaymentStatus.PENDING,
        )
        session = {
            "id": "cs_fulfill_keep",
            "payment_status": "unpaid",
            "status": "open",
            "payment_intent": None,
            "metadata": {"payment_method": Order.PaymentMethod.BANK},
        }

        result = OrderService.fulfill_stripe_session(session)

        order.refresh_from_db()
        self.assertEqual(result.id, order.id)
        self.assertEqual(order.payment_status, Order.PaymentStatus.PENDING)
        self.assertEqual(order.stripe_payment_intent_id, "")

    def test_unpaid_non_async_returns_none(self):
        draft = self._create_draft(session_id="cs_fulfill_ignore")
        session = {
            "id": "cs_fulfill_ignore",
            "payment_status": "unpaid",
            "status": "open",
            "metadata": {
                "draft_id": str(draft.id),
                "payment_method": Order.PaymentMethod.CARD,
            },
        }

        self.assertIsNone(OrderService.fulfill_stripe_session(session))
        self.assertFalse(
            Order.objects.filter(stripe_session_id="cs_fulfill_ignore").exists()
        )

    def test_missing_draft_id_returns_none(self):
        session = {
            "id": "cs_no_draft",
            "payment_status": "paid",
            "status": "complete",
            "metadata": {},
        }

        self.assertIsNone(OrderService.fulfill_stripe_session(session))

    def test_missing_draft_returns_none(self):
        session = {
            "id": "cs_missing_draft",
            "payment_status": "paid",
            "status": "complete",
            "metadata": {"draft_id": str(uuid4())},
        }

        self.assertIsNone(OrderService.fulfill_stripe_session(session))

    def test_assigns_customer_from_draft(self):
        draft = self._create_draft(
            session_id="cs_fulfill_customer",
            customer_id=self.customer.id,
        )
        session = {
            "id": "cs_fulfill_customer",
            "payment_status": "paid",
            "status": "complete",
            "payment_intent": "pi_customer",
            "metadata": {
                "draft_id": str(draft.id),
                "payment_method": Order.PaymentMethod.CARD,
            },
        }

        order = OrderService.fulfill_stripe_session(session)

        self.assertEqual(order.customer_id, self.customer.id)


class OrderServiceConfirmSessionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.item = baker.make(
            Item,
            name="Kabel",
            price=Decimal("10.00"),
            on_stock=10,
        )

    @patch("apps.orders.services.order.OrderService.fulfill_stripe_session")
    @patch("apps.orders.services.order.stripe.checkout.Session.retrieve")
    def test_confirm_returns_fulfilled_order(self, mock_retrieve, mock_fulfill):
        order = baker.make(
            Order,
            order_number="K39-2026-8100",
            email="buyer@example.com",
            stripe_session_id="cs_confirm_ok",
            payment_status=Order.PaymentStatus.PAID,
        )
        mock_retrieve.return_value = {"id": "cs_confirm_ok"}
        mock_fulfill.return_value = order

        result = OrderService.confirm_session("cs_confirm_ok")

        self.assertEqual(result.id, order.id)
        mock_retrieve.assert_called_once_with("cs_confirm_ok")
        mock_fulfill.assert_called_once()

    @patch("apps.orders.services.order.OrderService.fulfill_stripe_session")
    @patch("apps.orders.services.order.stripe.checkout.Session.retrieve")
    def test_confirm_returns_existing_when_fulfill_none(
        self, mock_retrieve, mock_fulfill
    ):
        order = baker.make(
            Order,
            order_number="K39-2026-8101",
            email="buyer@example.com",
            stripe_session_id="cs_confirm_existing",
            payment_status=Order.PaymentStatus.PENDING,
        )
        mock_retrieve.return_value = {"id": "cs_confirm_existing"}
        mock_fulfill.return_value = None

        result = OrderService.confirm_session("cs_confirm_existing")

        self.assertEqual(result.id, order.id)

    @patch("apps.orders.services.order.OrderService.fulfill_stripe_session")
    @patch("apps.orders.services.order.stripe.checkout.Session.retrieve")
    def test_confirm_raises_when_payment_incomplete(self, mock_retrieve, mock_fulfill):
        mock_retrieve.return_value = {"id": "cs_confirm_pending"}
        mock_fulfill.return_value = None

        with self.assertRaisesMessage(ValueError, "Zahlung noch nicht abgeschlossen."):
            OrderService.confirm_session("cs_confirm_pending")
