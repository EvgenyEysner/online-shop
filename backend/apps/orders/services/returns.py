import logging
from datetime import timedelta
from decimal import Decimal
from typing import Any

import stripe
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from apps.orders.models import Invoice, Item, Order, ReturnRequest, ReturnRequestItem
from apps.orders.services.credit_note import CreditNoteService
from apps.orders.services.pricing import PricingService

logger = logging.getLogger(__name__)

RETURN_WINDOW = timedelta(days=14)


class ReturnService:
    """
    Einzige Schreibstelle für den Rückgabe-/Widerruf-Workflow.
    """

    @staticmethod
    def can_request_return(order: Order) -> bool:
        if order.payment_status != Order.PaymentStatus.PAID:
            return False
        if order.delivered_at is None:
            return True
        return timezone.now() <= order.delivered_at + RETURN_WINDOW

    @staticmethod
    @transaction.atomic
    def create_request(
        order: Order, *, items: list[dict], reason: str
    ) -> ReturnRequest:
        if not ReturnService.can_request_return(order):
            raise ValidationError("Widerrufsfrist ist abgelaufen.")

        request = ReturnRequest.objects.create(order=order, reason=reason)
        for entry in items:
            order_item = entry["order_item"]
            if entry["quantity"] > order_item.quantity:
                raise ValidationError(
                    f"Menge übersteigt bestellte Menge für '{order_item.item_name}'."
                )
            ReturnRequestItem.objects.create(
                return_request=request,
                order_item=order_item,
                quantity=entry["quantity"],
            )
        return request

    @staticmethod
    @transaction.atomic
    def approve(request: ReturnRequest, *, actor: Any = None) -> ReturnRequest:
        if request.status != ReturnRequest.Status.REQUESTED:
            raise ValidationError("Nur angefragte Rückgaben können genehmigt werden.")
        request.status = ReturnRequest.Status.APPROVED
        request.decided_at = timezone.now()
        request.decided_by = actor
        request.save(update_fields=["status", "decided_at", "decided_by"])
        logger.info("Rückgabe #%s genehmigt (actor=%s).", request.pk, actor)
        return request

    @staticmethod
    @transaction.atomic
    def reject(
        request: ReturnRequest, *, actor: Any = None, note: str = ""
    ) -> ReturnRequest:
        if request.status != ReturnRequest.Status.REQUESTED:
            raise ValidationError("Nur angefragte Rückgaben können abgelehnt werden.")
        request.status = ReturnRequest.Status.REJECTED
        request.decided_at = timezone.now()
        request.decided_by = actor
        request.rejection_note = note
        request.save(
            update_fields=["status", "decided_at", "decided_by", "rejection_note"]
        )
        logger.info(
            "Rückgabe #%s abgelehnt (actor=%s, Grund=%r).", request.pk, actor, note
        )
        return request

    @staticmethod
    @transaction.atomic
    def complete_return(request: ReturnRequest, *, actor: Any = None) -> ReturnRequest:
        if request.status != ReturnRequest.Status.APPROVED:
            raise ValidationError("Nur genehmigte Rückgaben können erstattet werden.")
        if request.refunded_at is not None:
            # Idempotenz-Schutz gegen Doppelerstattung request.status ist zu diesem Zeitpunkt bereits
            # REFUNDED, der obige Status Check greift daher normalerweise
            # schon vorher dieser zweite Check bleibt als explizite,
            # eigenständige Absicherung gegen den Doppel-Refund selbst
            # bestehen, unabhängig davon, wie der Status-Guard implementiert
            # ist.
            return request

        net, tax, total = ReturnService._calculate_refund_amount(request)
        order = request.order

        if order.stripe_payment_intent_id:
            stripe.Refund.create(
                payment_intent=order.stripe_payment_intent_id,
                amount=int(total * Decimal("100")),
            )
        else:
            logger.warning(
                "Rückgabe #%s ohne stripe_payment_intent_id auf Order %s - "
                "kein Stripe-Refund ausgeführt.",
                request.pk,
                order.order_number,
            )

        original_invoice = order.invoices.get(
            document_type=Invoice.DocumentType.INVOICE
        )
        CreditNoteService.issue_credit_note(
            original_invoice,
            net_amount=net,
            tax_amount=tax,
            total_amount=total,
            reason=f"Rückgabe #{request.pk}",
            actor=actor,
        )

        ReturnService._restock_returned_items(request)

        request.status = ReturnRequest.Status.REFUNDED
        request.refunded_at = timezone.now()
        request.save(update_fields=["status", "refunded_at"])
        logger.info(
            "Rückgabe #%s erstattet (Betrag=%s, actor=%s).",
            request.pk,
            total,
            actor,
        )
        return request

    @staticmethod
    def _calculate_refund_amount(
        request: ReturnRequest,
    ) -> tuple[Decimal, Decimal, Decimal]:
        """
        Proportionale Erstattung: Netto-Anteil je Rückgabeposition ist
        Menge x OrderItem.unit_price (unit_price ist bereits der
        Netto-Einzelpreis, siehe OrderCreationService/PricingService, die
        unit_price direkt aus Item.price - ohne Steuer - befüllen).
        """
        net = sum(
            (
                PricingService.money(entry.order_item.unit_price * entry.quantity)
                for entry in request.items.select_related("order_item").all()
            ),
            Decimal("0.00"),
        )
        tax = PricingService.money(net * settings.TAX_RATE)
        total = PricingService.money(net + tax)
        return net, tax, total

    @staticmethod
    def _restock_returned_items(request: ReturnRequest) -> None:
        """
        Erhöht Item.on_stock für die zurückgegebenen Mengen. Gleiches
        select_for_update-Sperrmuster wie
        OrderCreationService.restock_order().
        """
        items = list(request.items.select_related("order_item__item").all())
        item_ids = sorted(
            {entry.order_item.item_id for entry in items if entry.order_item.item_id}
        )
        if not item_ids:
            return

        list(Item.objects.select_for_update().filter(pk__in=item_ids))

        for entry in items:
            item_id = entry.order_item.item_id
            if item_id is None:
                continue  # Artikel wurde inzwischen gelöscht, nichts restockbar
            Item.objects.filter(pk=item_id).update(
                on_stock=F("on_stock") + entry.quantity
            )
