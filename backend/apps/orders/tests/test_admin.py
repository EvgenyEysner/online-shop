from django.apps import apps
from django.contrib import admin
from django.test import SimpleTestCase

from apps.core.models import GlobalIdentifier
from apps.orders.models import Category, CheckoutDraft, Item, Order, OrderItem


class ShopModelAdminRegistrationTests(SimpleTestCase):

    def test_category_is_registered(self):
        self.assertIn(Category, admin.site._registry)

    def test_item_is_registered(self):
        self.assertIn(Item, admin.site._registry)

    def test_order_is_registered(self):
        self.assertIn(Order, admin.site._registry)

    def test_global_identifier_is_registered(self):
        self.assertIn(GlobalIdentifier, admin.site._registry)

    def test_checkout_draft_is_not_registered(self):
        self.assertNotIn(CheckoutDraft, admin.site._registry)

    def test_order_item_is_not_registered_as_own_model(self):
        # OrderItem wird bewusst nur als Inline in OrderAdmin verwaltet,
        # nicht als eigenständiges Top-Level-Admin-Modell.
        self.assertNotIn(OrderItem, admin.site._registry)


class OrderAdminConfigurationTests(SimpleTestCase):
    """
    OrderItem als Inline, Preis-Snapshot-Felder readonly (historische Buchhaltungsdaten
    dürfen nicht nachträglich über den Admin verfälscht werden).
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.order_admin = admin.site._registry[Order]

    def test_order_item_is_registered_as_inline(self):
        inline_models = [inline.model for inline in self.order_admin.inlines]
        self.assertIn(OrderItem, inline_models)

    def test_price_snapshot_fields_are_readonly(self):
        for field in ("subtotal", "tax_amount", "shipping_cost", "total"):
            self.assertIn(field, self.order_admin.readonly_fields)

    def test_stripe_ids_are_readonly(self):
        for field in ("stripe_session_id", "stripe_payment_intent_id"):
            self.assertIn(field, self.order_admin.readonly_fields)


class GlobalIdentifierAdminConfigurationTests(SimpleTestCase):
    def test_key_and_value_are_readonly(self):
        identifier_admin = admin.site._registry[GlobalIdentifier]
        self.assertIn("key", identifier_admin.readonly_fields)
        self.assertIn("value", identifier_admin.readonly_fields)
