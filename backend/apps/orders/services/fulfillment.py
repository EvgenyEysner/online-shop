import logging
from typing import Any

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.orders.models import Order, OrderStatusHistory

logger = logging.getLogger(__name__)


class FulfillmentService:
    """
    Einzige zulässige Schreibstelle für Order.fulfillment_status.
    """

    @staticmethod
    @transaction.atomic
    def update_status(
        order: Order,
        new_status: str,
        *,
        tracking_number: str = "",
        carrier: str = "",
        actor: Any = None,
        note: str = "",
    ) -> Order:
        """
        Setzt fulfillment_status (+ optional tracking_number/carrier) und
        protokolliert den Übergang in OrderStatusHistory. Versandstatus
        kann erst nach Zahlungseingang gepflegt werden, da ein Versand vor
        Zahlung im bestehenden CheckoutFlow nicht vorgesehen ist.
        """
        if order.payment_status != Order.PaymentStatus.PAID:
            raise ValidationError(
                "Versandstatus kann erst nach Zahlungseingang gepflegt werden."
            )

        old_status = order.fulfillment_status
        # Zustand VOR dem Setzen von shipped_at festhalten:
        # verhindert Doppel-Versand der Benachrichtigung, wenn tracking_number/
        # carrier später korrigiert werden, während der Status bereits
        # SHIPPED bleibt.
        was_already_shipped = order.shipped_at is not None
        order.fulfillment_status = new_status
        if tracking_number:
            order.tracking_number = tracking_number
        if carrier:
            order.carrier = carrier
        if new_status == Order.FulfillmentStatus.SHIPPED and not order.shipped_at:
            order.shipped_at = timezone.now()
        if new_status == Order.FulfillmentStatus.DELIVERED and not order.delivered_at:
            order.delivered_at = timezone.now()

        order.save(
            update_fields=[
                "fulfillment_status",
                "tracking_number",
                "carrier",
                "shipped_at",
                "delivered_at",
            ]
        )
        OrderStatusHistory.objects.create(
            order=order,
            status_type=OrderStatusHistory.StatusType.FULFILLMENT,
            old_value=old_status,
            new_value=new_status,
            changed_by=actor,
            note=note,
        )
        logger.info(
            "Order %s Versandstatus %s -> %s (actor=%s).",
            order.order_number,
            old_status,
            new_status,
            actor,
        )

        # Versand-Benachrichtigung nur beim tatsächlichen
        # Übergang zu SHIPPED, nicht bei einer späteren Korrektur von
        # tracking_number/carrier während der Status bereits SHIPPED ist.
        if new_status == Order.FulfillmentStatus.SHIPPED and not was_already_shipped:
            from apps.orders.tasks import send_shipping_notification_email

            send_shipping_notification_email.delay(order.pk)

        return order
