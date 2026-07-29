from decimal import Decimal
from typing import Any

import stripe
from django.conf import settings

from apps.orders.models import Order
from apps.utils.helpers import stripe_get
from .pricing import PricingService


class StripeCheckoutService:
    """
    Kapselt alle Interaktionen mit Stripe Checkout Sessions.
    """

    PAYMENT_METHOD_TYPES: dict[str, list[str]] = {
        Order.PaymentMethod.CARD: ["card"],
        Order.PaymentMethod.PAYPAL: ["paypal"],
        Order.PaymentMethod.BANK: ["customer_balance"],
        Order.PaymentMethod.INVOICE: ["customer_balance"],
    }
    ASYNC_PAYMENT_METHODS = {
        Order.PaymentMethod.BANK,
        Order.PaymentMethod.INVOICE,
    }

    def __init__(self):
        stripe.api_key = settings.STRIPE_SECRET_KEY

    @staticmethod
    def to_cents(value: Decimal) -> int:
        return int(PricingService.money(value) * 100)

    def is_async_payment_method(self, payment_method: str) -> bool:
        return payment_method in self.ASYNC_PAYMENT_METHODS

    def _resolve_payment_method_types(self, payment_method: str) -> list[str]:
        try:
            return self.PAYMENT_METHOD_TYPES[payment_method]
        except KeyError:
            raise ValueError(
                f"Unbekannte Zahlungsmethode: {payment_method!r}"
            ) from None

    def _build_line_items(self, cart_items: list[dict], totals: dict) -> list[dict]:
        line_items = [
            {
                "quantity": entry["quantity"],
                "price_data": {
                    # Todo make currency dynamic
                    "currency": "eur",
                    "unit_amount": self.to_cents(
                        PricingService.money(
                            entry["item"].price * (Decimal("1") + settings.TAX_RATE)
                        )
                    ),
                    "product_data": self._product_data(entry["item"]),
                },
            }
            for entry in cart_items
        ]

        if totals["shipping_cost"] > 0:
            line_items.append(
                {
                    "quantity": 1,
                    "price_data": {
                        "currency": "eur",
                        "unit_amount": self.to_cents(totals["shipping_cost"]),
                        "product_data": {"name": "Versand"},
                    },
                }
            )
        return line_items

    @staticmethod
    def _product_data(item) -> dict:
        product_data = {"name": item.name}
        description = (item.description or "").strip()
        if description:
            product_data["description"] = description[:200]
        return product_data

    def _create_stripe_customer(self, *, payload: dict, draft_id) -> str:
        shipping = payload.get("shipping") or {}
        customer_name = (
            " ".join(
                part
                for part in (
                    shipping.get("first_name", ""),
                    shipping.get("last_name", ""),
                )
                if part
            ).strip()
            or None
        )
        stripe_customer = stripe.Customer.create(
            email=payload["email"],
            name=customer_name,
            phone=payload.get("phone") or None,
            metadata={
                "draft_id": str(draft_id),
                "shop_user_id": str(payload.get("customer_id") or ""),
            },
        )
        return stripe_customer.id

    def create_session(
        self,
        *,
        cart_items: list[dict],
        totals: dict,
        payload: dict,
        draft_id,
        success_url: str,
        cancel_url: str,
    ) -> stripe.checkout.Session:
        payment_method = payload.get("payment_method", Order.PaymentMethod.CARD)

        session_kwargs: dict[str, Any] = {
            "mode": "payment",
            "line_items": self._build_line_items(cart_items, totals),
            "success_url": success_url,
            "cancel_url": cancel_url,
            "payment_method_types": self._resolve_payment_method_types(payment_method),
            "metadata": {
                "draft_id": str(draft_id),
                "payment_method": payment_method,
            },
            "payment_intent_data": {
                "metadata": {
                    "draft_id": str(draft_id),
                    "payment_method": payment_method,
                }
            },
        }

        if self.is_async_payment_method(payment_method):
            session_kwargs["customer"] = self._create_stripe_customer(
                payload=payload, draft_id=draft_id
            )
            session_kwargs["payment_method_options"] = {
                "customer_balance": {
                    "funding_type": "bank_transfer",
                    "bank_transfer": {
                        "type": "eu_bank_transfer",
                        "eu_bank_transfer": {"country": "DE"},
                    },
                }
            }
        else:
            session_kwargs["customer_email"] = payload["email"]

        return stripe.checkout.Session.create(**session_kwargs)

    # --- Auslesen von Session-/Webhook-Daten -----------------------------

    @staticmethod
    def get(obj, key: str, default=None):
        """Liest ein Feld aus Session, Metadata oder PaymentIntent."""
        return stripe_get(obj, key, default)

    @staticmethod
    def extract_payment_intent_id(payment_intent) -> str:
        if isinstance(payment_intent, str):
            return payment_intent
        return stripe_get(payment_intent, "id", "") or ""
