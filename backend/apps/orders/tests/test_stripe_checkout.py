from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings
from model_bakery import baker

from apps.orders.models import Item, Order
from apps.orders.services.stripe_checkout import StripeCheckoutService


class BuildLineItemsCurrencyTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.item = baker.make(
            Item, name="Solarmodul", price=Decimal("100.00"), on_stock=5
        )

    def setUp(self):
        self.service = StripeCheckoutService()

    @staticmethod
    def _cart_items(item, quantity=1):
        return [{"item": item, "quantity": quantity}]

    @staticmethod
    def _totals(shipping_cost=Decimal("0.00")):
        return {"shipping_cost": shipping_cost}

    def test_item_line_uses_default_currency_eur(self):
        line_items = self.service._build_line_items(
            self._cart_items(self.item), self._totals()
        )

        self.assertEqual(line_items[0]["price_data"]["currency"], "eur")

    def test_shipping_line_uses_default_currency_eur(self):
        line_items = self.service._build_line_items(
            self._cart_items(self.item),
            self._totals(shipping_cost=Decimal("4.90")),
        )

        shipping_line = next(
            line
            for line in line_items
            if line["price_data"]["product_data"].get("name") == "Versand"
        )
        self.assertEqual(shipping_line["price_data"]["currency"], "eur")

    @override_settings(CURRENCY="usd")
    def test_item_line_uses_configured_currency(self):
        line_items = self.service._build_line_items(
            self._cart_items(self.item), self._totals()
        )

        self.assertEqual(line_items[0]["price_data"]["currency"], "usd")

    @override_settings(CURRENCY="usd")
    def test_shipping_line_uses_configured_currency(self):
        line_items = self.service._build_line_items(
            self._cart_items(self.item),
            self._totals(shipping_cost=Decimal("4.90")),
        )

        shipping_line = next(
            line
            for line in line_items
            if line["price_data"]["product_data"].get("name") == "Versand"
        )
        self.assertEqual(shipping_line["price_data"]["currency"], "usd")

    @override_settings(CURRENCY="usd")
    def test_no_shipping_line_added_when_shipping_free(self):
        line_items = self.service._build_line_items(
            self._cart_items(self.item), self._totals(shipping_cost=Decimal("0.00"))
        )

        self.assertEqual(len(line_items), 1)


@override_settings(CURRENCY="usd")
class CreateSessionCurrencyIntegrationTests(TestCase):
    """
    Verifiziert mit gemocktem Stripe-Client, dass settings.CURRENCY
    tatsächlich bis in den an Stripe gesendeten Session-Request
    durchgereicht wird.
    """

    @classmethod
    def setUpTestData(cls):
        cls.item = baker.make(
            Item, name="Wechselrichter", price=Decimal("200.00"), on_stock=5
        )

    @patch("apps.orders.services.stripe_checkout.stripe.checkout.Session.create")
    def test_create_session_passes_configured_currency_to_stripe(self, mock_create):
        mock_create.return_value = MagicMock(
            id="cs_currency", url="https://checkout.stripe.com/c/pay/cs_currency"
        )
        service = StripeCheckoutService()

        service.create_session(
            cart_items=[{"item": self.item, "quantity": 1}],
            totals={"shipping_cost": Decimal("0.00")},
            payload={
                "email": "buyer@example.com",
                "payment_method": Order.PaymentMethod.CARD,
            },
            draft_id="draft-currency-1",
            success_url="https://shop.example/checkout?session_id={CHECKOUT_SESSION_ID}",
            cancel_url="https://shop.example/checkout?cancelled=1",
        )

        sent_line_items = mock_create.call_args.kwargs["line_items"]
        self.assertTrue(
            all(line["price_data"]["currency"] == "usd" for line in sent_line_items)
        )
