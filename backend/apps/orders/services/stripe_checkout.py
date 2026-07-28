from decimal import Decimal, ROUND_HALF_UP
from uuid import uuid4

import stripe
from django.conf import settings
from django.db import transaction

from apps.accounts.services.identifiers import allocate_order_number
from apps.orders.models import CheckoutDraft, Item, Order, OrderItem

stripe.api_key = settings.STRIPE_SECRET_KEY

TAX_RATE = Decimal("0.19")
FREE_SHIPPING_THRESHOLD = Decimal("500.00")
SHIPPING_COST = Decimal("4.90")

PAYMENT_METHOD_TYPES = {
    Order.PaymentMethod.CARD: ["card"],
    Order.PaymentMethod.PAYPAL: ["paypal"],
    Order.PaymentMethod.BANK: ["customer_balance"],
    Order.PaymentMethod.INVOICE: ["customer_balance"],
}


def money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def to_cents(value: Decimal) -> int:
    return int((money(value) * 100).to_integral_value(rounding=ROUND_HALF_UP))


def calculate_totals(cart_items: list[dict]) -> dict[str, Decimal]:
    subtotal = Decimal("0.00")
    for entry in cart_items:
        item = entry["item"]
        qty = Decimal(entry["quantity"])
        subtotal += money(item.price * qty)

    shipping = (
        Decimal("0.00") if subtotal >= FREE_SHIPPING_THRESHOLD else SHIPPING_COST
    )
    tax_amount = money(subtotal * TAX_RATE)
    total = money(subtotal + tax_amount + shipping)
    return {
        "subtotal": money(subtotal),
        "tax_amount": tax_amount,
        "shipping_cost": money(shipping),
        "total": total,
    }


def resolve_cart_items(raw_items: list[dict]) -> list[dict]:
    resolved = []
    for entry in raw_items:
        item = entry["item"]
        if not isinstance(item, Item):
            item = Item.objects.get(pk=item)
        resolved.append({"item": item, "quantity": int(entry["quantity"])})
    return resolved


class OrderService:
    @staticmethod
    @transaction.atomic
    def create_order_from_payload(
        *,
        payload: dict,
        stripe_session_id: str,
        stripe_payment_intent_id: str = "",
        customer=None,
        payment_status: str = Order.PaymentStatus.PAID,
    ) -> Order:
        existing = (
            Order.objects.select_related("customer")
            .prefetch_related("items")
            .filter(stripe_session_id=stripe_session_id)
            .first()
        )
        if existing:
            return existing

        raw_items = payload["items"]
        cart_items = resolve_cart_items(raw_items)
        totals = calculate_totals(cart_items)
        shipping = payload["shipping"]
        billing = payload.get("billing") or shipping
        same_as_shipping = bool(payload.get("billing_same_as_shipping", True))

        order = Order.objects.create(
            order_number=allocate_order_number(),
            customer=customer,
            email=payload["email"],
            phone=payload.get("phone", ""),
            note=payload.get("note") or "",
            shipping_salutation=shipping.get("salutation", ""),
            shipping_first_name=shipping["first_name"],
            shipping_last_name=shipping["last_name"],
            shipping_company=shipping.get("company", ""),
            shipping_street=shipping["street"],
            shipping_street_no=shipping.get("street_no", ""),
            shipping_zip=shipping["zip"],
            shipping_city=shipping["city"],
            shipping_country=shipping.get("country", "Deutschland"),
            billing_same_as_shipping=same_as_shipping,
            billing_salutation=billing.get("salutation", ""),
            billing_first_name=billing.get("first_name", ""),
            billing_last_name=billing.get("last_name", ""),
            billing_company=billing.get("company", ""),
            billing_street=billing.get("street", ""),
            billing_street_no=billing.get("street_no", ""),
            billing_zip=billing.get("zip", ""),
            billing_city=billing.get("city", ""),
            billing_country=billing.get("country", ""),
            payment_method=payload.get("payment_method", Order.PaymentMethod.CARD),
            payment_status=payment_status,
            stripe_session_id=stripe_session_id,
            stripe_payment_intent_id=stripe_payment_intent_id or "",
            subtotal=totals["subtotal"],
            tax_amount=totals["tax_amount"],
            shipping_cost=totals["shipping_cost"],
            total=totals["total"],
        )

        OrderItem.objects.bulk_create(
            [
                OrderItem(
                    order=order,
                    item=entry["item"],
                    item_name=entry["item"].name,
                    unit_price=entry["item"].price,
                    quantity=entry["quantity"],
                )
                for entry in cart_items
            ]
        )

        return (
            Order.objects.select_related("customer")
            .prefetch_related("items__item")
            .get(pk=order.pk)
        )

    @staticmethod
    def create_checkout_session(
        *,
        payload: dict,
        customer=None,
        success_url: str,
        cancel_url: str,
    ) -> dict:
        cart_items = resolve_cart_items(payload["items"])
        totals = calculate_totals(cart_items)
        payment_method = payload.get("payment_method", Order.PaymentMethod.CARD)
        method_types = PAYMENT_METHOD_TYPES.get(payment_method, ["card"])

        draft = CheckoutDraft.objects.create(
            id=uuid4(),
            payload={
                **payload,
                "items": [
                    {"item": entry["item"].pk, "quantity": entry["quantity"]}
                    for entry in cart_items
                ],
                "customer_id": getattr(customer, "id", None),
                "totals": {k: str(v) for k, v in totals.items()},
            },
        )

        line_items = []
        for entry in cart_items:
            unit_gross = money(entry["item"].price * (Decimal("1") + TAX_RATE))
            product_data = {"name": entry["item"].name}
            description = (entry["item"].description or "").strip()
            if description:
                product_data["description"] = description[:200]
            line_items.append(
                {
                    "quantity": entry["quantity"],
                    "price_data": {
                        "currency": "eur",
                        "unit_amount": to_cents(unit_gross),
                        "product_data": product_data,
                    },
                }
            )

        if totals["shipping_cost"] > 0:
            line_items.append(
                {
                    "quantity": 1,
                    "price_data": {
                        "currency": "eur",
                        "unit_amount": to_cents(totals["shipping_cost"]),
                        "product_data": {"name": "Versand"},
                    },
                }
            )

        session_kwargs = {
            "mode": "payment",
            "customer_email": payload["email"],
            "line_items": line_items,
            "success_url": success_url,
            "cancel_url": cancel_url,
            "payment_method_types": method_types,
            "metadata": {
                "draft_id": str(draft.id),
                "payment_method": payment_method,
            },
            "payment_intent_data": {
                "metadata": {
                    "draft_id": str(draft.id),
                    "payment_method": payment_method,
                }
            },
        }

        if payment_method in (
            Order.PaymentMethod.BANK,
            Order.PaymentMethod.INVOICE,
        ):
            session_kwargs["payment_method_options"] = {
                "customer_balance": {
                    "funding_type": "bank_transfer",
                    "bank_transfer": {"type": "eu_bank_transfer", "eu_bank_transfer": {"country": "DE"}},
                }
            }

        session = stripe.checkout.Session.create(**session_kwargs)
        draft.stripe_session_id = session.id
        draft.save(update_fields=["stripe_session_id"])

        return {
            "session_id": session.id,
            "url": session.url,
            "draft_id": str(draft.id),
            "public_key": settings.STRIPE_PUBLIC_KEY,
        }

    @staticmethod
    def fulfill_stripe_session(session: dict | stripe.checkout.Session) -> Order | None:
        session_id = session["id"] if isinstance(session, dict) else session.id
        payment_status = (
            session["payment_status"]
            if isinstance(session, dict)
            else session.payment_status
        )
        metadata = (
            session.get("metadata") or {}
            if isinstance(session, dict)
            else (session.metadata or {})
        )
        payment_intent = (
            session.get("payment_intent")
            if isinstance(session, dict)
            else session.payment_intent
        )

        if payment_status not in ("paid", "no_payment_required"):
            # Bank transfer may be unpaid initially; still create order as pending.
            if payment_status != "unpaid":
                return None

        draft_id = metadata.get("draft_id")
        if not draft_id:
            return None

        draft = CheckoutDraft.objects.filter(pk=draft_id).first()
        if not draft:
            existing = Order.objects.filter(stripe_session_id=session_id).first()
            return existing

        customer = None
        customer_id = draft.payload.get("customer_id")
        if customer_id:
            from django.contrib.auth import get_user_model

            User = get_user_model()
            customer = User.objects.filter(pk=customer_id).first()

        status = (
            Order.PaymentStatus.PAID
            if payment_status in ("paid", "no_payment_required")
            else Order.PaymentStatus.PENDING
        )
        intent_id = ""
        if isinstance(payment_intent, str):
            intent_id = payment_intent
        elif payment_intent:
            intent_id = getattr(payment_intent, "id", "") or ""

        order = OrderService.create_order_from_payload(
            payload=draft.payload,
            stripe_session_id=session_id,
            stripe_payment_intent_id=intent_id,
            customer=customer,
            payment_status=status,
        )
        return order

    @staticmethod
    def confirm_session(session_id: str) -> Order:
        session = stripe.checkout.Session.retrieve(session_id)
        order = OrderService.fulfill_stripe_session(session)
        if order is None:
            raise ValueError("Zahlung noch nicht abgeschlossen.")
        return order
