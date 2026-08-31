from dataclasses import dataclass
from datetime import datetime

from django.db.models import Prefetch

from apps.orders.models import Invoice, Order


@dataclass(frozen=True)
class NotificationEvent:
    kind: str  # "order_created" | "order_paid" | "order_shipped" |
    # "order_delivered" | "invoice_issued" | "return_status_changed"
    order_id: int
    order_number: str
    occurred_at: datetime
    message: str


class NotificationService:
    """
    Dashboard-Benachrichtigungsglocke.
    """

    @staticmethod
    def get_recent_events(user, *, limit: int = 20) -> list[NotificationEvent]:
        # Invoice-Prefetch bereits auf document_type=invoice gefiltert
        # (statt order.invoices.filter(...) erst nach dem Prefetch
        # aufzurufen), damit pro Order keine zusätzliche Query anfällt.
        orders = Order.objects.filter(customer=user).prefetch_related(
            Prefetch(
                "invoices",
                queryset=Invoice.objects.filter(
                    document_type=Invoice.DocumentType.INVOICE
                ),
            ),
            "return_requests",
        )

        events: list[NotificationEvent] = []
        for order in orders:
            events.append(
                NotificationEvent(
                    "order_created",
                    order.pk,
                    order.order_number,
                    order.created_at,
                    f"Bestellung {order.order_number} eingegangen",
                )
            )
            if order.paid_at:
                events.append(
                    NotificationEvent(
                        "order_paid",
                        order.pk,
                        order.order_number,
                        order.paid_at,
                        f"Zahlung für {order.order_number} erhalten",
                    )
                )
            if order.shipped_at:
                events.append(
                    NotificationEvent(
                        "order_shipped",
                        order.pk,
                        order.order_number,
                        order.shipped_at,
                        f"{order.order_number} wurde versandt",
                    )
                )
            if order.delivered_at:
                events.append(
                    NotificationEvent(
                        "order_delivered",
                        order.pk,
                        order.order_number,
                        order.delivered_at,
                        f"{order.order_number} wurde zugestellt",
                    )
                )
            for invoice in order.invoices.all():
                events.append(
                    NotificationEvent(
                        "invoice_issued",
                        order.pk,
                        order.order_number,
                        invoice.issued_at,
                        f"Rechnung {invoice.invoice_number} verfügbar",
                    )
                )
            for return_request in order.return_requests.all():
                events.append(
                    NotificationEvent(
                        "return_status_changed",
                        order.pk,
                        order.order_number,
                        return_request.decided_at or return_request.requested_at,
                        f"Rückgabe für {order.order_number}: "
                        f"{return_request.get_status_display()}",
                    )
                )

        events.sort(key=lambda event: event.occurred_at, reverse=True)
        return events[:limit]
