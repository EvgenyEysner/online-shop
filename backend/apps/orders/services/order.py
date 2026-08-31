import logging
from typing import Any
from uuid import uuid4

import stripe
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.orders.exceptions import InsufficientStockError
from apps.orders.models import CheckoutDraft, Order, OrderStatusHistory

from .order_creation import OrderCreationService
from .pricing import PricingService
from .stripe_checkout import StripeCheckoutService

logger = logging.getLogger(__name__)


class OrderService:
    """
    Orchestriert den Checkout-Flow: Draft anlegen, Stripe-Session
    erzeugen, Order-Erstellung bei erfolgreicher/pending Zahlung anstoßen.
    """

    @staticmethod
    @transaction.atomic
    def mark_as_paid(order: Order, *, actor: Any = None) -> Order:
        """
        Einzige, zentrale Stelle, die eine Order als bezahlt markiert wird.
        """
        from apps.orders.services.invoice import InvoiceService

        if order.payment_status != Order.PaymentStatus.PAID:
            old_status = order.payment_status
            order.payment_status = Order.PaymentStatus.PAID
            order.paid_at = timezone.now()
            order.save(update_fields=["payment_status", "paid_at"])
            OrderStatusHistory.objects.create(
                order=order,
                status_type=OrderStatusHistory.StatusType.PAYMENT,
                old_value=old_status,
                new_value=Order.PaymentStatus.PAID,
                changed_by=actor,
            )
            logger.info(
                "Order %s als bezahlt markiert (actor=%s).",
                order.order_number,
                actor,
            )

        InvoiceService.ensure_invoice_for_order(order)
        return order

    @staticmethod
    def create_checkout_session(
        *, payload: dict, customer=None, success_url: str, cancel_url: str
    ) -> dict:
        cart_items = PricingService.resolve_cart_items(payload["items"])
        totals = PricingService.calculate_totals(cart_items)

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

        checkout = StripeCheckoutService()
        session = checkout.create_session(
            cart_items=cart_items,
            totals=totals,
            payload=payload,
            draft_id=draft.id,
            success_url=success_url,
            cancel_url=cancel_url,
        )

        draft.stripe_session_id = session.id
        draft.save(update_fields=["stripe_session_id"])

        payment_method = payload.get("payment_method", Order.PaymentMethod.CARD)
        if checkout.is_async_payment_method(payment_method):
            try:
                # Überweisung/Rechnung: Bestellung sofort als pending
                # speichern, inkl. Lagerbestands-Reservierung.
                OrderCreationService.create_from_payload(
                    payload=draft.payload,
                    stripe_session_id=session.id,
                    customer=customer,
                    payment_status=Order.PaymentStatus.PENDING,
                )
            except InsufficientStockError:
                # Die Stripe-Session existiert bereits, kann aber nicht mehr
                # erfüllt werden - verfallen lassen, damit sie nicht offen
                # im Stripe-Dashboard hängen bleibt, Fehler weiterreichen.
                stripe.checkout.Session.expire(session.id)
                raise

        return {
            "session_id": session.id,
            "url": session.url,
            "draft_id": str(draft.id),
            "public_key": settings.STRIPE_PUBLIC_KEY,
        }

    @staticmethod
    def _create_order_or_refund(
        *,
        payload: dict,
        stripe_session_id: str,
        stripe_payment_intent_id: str,
        payment_status: str,
        customer=None,
    ) -> Order | None:
        """
        Wrapper um OrderCreationService.create_from_payload für den
        Webhook-Pfad. Falls der Bestand inzwischen nicht mehr ausreicht,
        obwohl die Zahlung (bei Kartenzahlung) bereits erfolgt ist, wird
        automatisch erstattet, statt die Order stillschweigend nicht
        anzulegen.
        """
        try:
            return OrderCreationService.create_from_payload(
                payload=payload,
                stripe_session_id=stripe_session_id,
                stripe_payment_intent_id=stripe_payment_intent_id,
                customer=customer,
                payment_status=payment_status,
            )
        except InsufficientStockError:
            logger.error(
                "Lagerbestand reicht nicht mehr aus für Stripe-Session %s "
                "trotz abgeschlossener Zahlung (payment_status=%s) – "
                "erstatte automatisch.",
                stripe_session_id,
                payment_status,
            )
            if payment_status == Order.PaymentStatus.PAID and stripe_payment_intent_id:
                stripe.Refund.create(payment_intent=stripe_payment_intent_id)
            return None

    @staticmethod
    def fulfill_stripe_session(session: dict | stripe.checkout.Session) -> Order | None:
        checkout = StripeCheckoutService()

        session_id = checkout.get(session, "id")
        payment_status = checkout.get(session, "payment_status")
        session_status = checkout.get(session, "status")
        metadata = checkout.get(session, "metadata") or {}
        payment_intent = checkout.get(session, "payment_intent")
        payment_method = checkout.get(metadata, "payment_method")
        intent_id = checkout.extract_payment_intent_id(payment_intent)

        is_paid = payment_status in ("paid", "no_payment_required")
        is_async_pending = payment_status == "unpaid" and (
            payment_method in checkout.ASYNC_PAYMENT_METHODS
            or session_status == "complete"
        )

        existing = Order.objects.filter(stripe_session_id=session_id).first()
        if existing:
            if is_paid:
                return OrderService._create_order_or_refund(
                    payload={},
                    stripe_session_id=session_id,
                    stripe_payment_intent_id=intent_id,
                    payment_status=Order.PaymentStatus.PAID,
                )
            return existing

        if not is_paid and not is_async_pending:
            return None

        draft_id = checkout.get(metadata, "draft_id")
        if not draft_id:
            return None

        draft = CheckoutDraft.objects.filter(pk=draft_id).first()
        if not draft:
            return None

        customer = None
        customer_id = draft.payload.get("customer_id")
        if customer_id:
            from django.contrib.auth import get_user_model

            User = get_user_model()
            customer = User.objects.filter(pk=customer_id).first()

        return OrderService._create_order_or_refund(
            payload=draft.payload,
            stripe_session_id=session_id,
            stripe_payment_intent_id=intent_id,
            customer=customer,
            payment_status=(
                Order.PaymentStatus.PAID if is_paid else Order.PaymentStatus.PENDING
            ),
        )

    @staticmethod
    def confirm_session(session_id: str) -> Order:
        existing = Order.objects.filter(stripe_session_id=session_id).first()
        session = stripe.checkout.Session.retrieve(session_id)
        order = OrderService.fulfill_stripe_session(session)
        if order is None:
            if existing is not None:
                return existing
            raise ValueError("Zahlung noch nicht abgeschlossen.")
        return (
            Order.objects.select_related("customer")
            .prefetch_related("items__item")
            .get(pk=order.pk)
        )
