from typing import Any

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils import timezone


@shared_task(
    bind=True,
    max_retries=5,
    default_retry_delay=60,
    autoretry_for=(Exception,),
)
def send_invoice_email(self: Any, invoice_id: int) -> None:
    from apps.orders.models import Invoice

    invoice = Invoice.objects.select_related("order").get(pk=invoice_id)
    if invoice.sent_at is not None:
        # --- bereits versendet (z. B. Retry nach Absturz kurz vor Commit)
        return

    subject = (
        f"Ihre Rechnung {invoice.invoice_number}"
        if invoice.document_type == Invoice.DocumentType.INVOICE
        else f"Ihre Gutschrift {invoice.invoice_number}"
    )
    body = (
        "Anbei Ihre Rechnung als PDF. Vielen Dank für Ihren Einkauf!"
        if invoice.document_type == Invoice.DocumentType.INVOICE
        else "Anbei Ihre Gutschrift/Korrekturrechnung als PDF."
    )

    message = EmailMessage(
        subject=subject,
        body=body,
        to=[invoice.order.email],
    )
    message.attach(
        f"{invoice.invoice_number}.pdf", invoice.pdf_file.read(), "application/pdf"
    )
    message.send()
    invoice.sent_at = timezone.now()
    invoice.save(update_fields=["sent_at"])


@shared_task(
    bind=True,
    max_retries=5,
    default_retry_delay=60,
    autoretry_for=(Exception,),
)
def send_order_confirmation_email(self: Any, order_id: int) -> None:
    """
    Bestellbestätigung, ausgelöst sofort bei Order-Erstellung, unabhängig
    vom Zahlungsstatus.
    """
    from apps.orders.models import Order

    order = Order.objects.prefetch_related("items").get(pk=order_id)
    if order.confirmation_sent_at is not None:
        # --- bereits versendet (z. B. Retry nach Absturz kurz vor Commit)
        return

    EmailMessage(
        subject=f"Bestellbestätigung {order.order_number}",
        body=render_to_string("orders/emails/order_confirmation.txt", {"order": order}),
        to=[order.email],
    ).send()
    order.confirmation_sent_at = timezone.now()
    order.save(update_fields=["confirmation_sent_at"])


@shared_task(
    bind=True,
    max_retries=5,
    default_retry_delay=60,
    autoretry_for=(Exception,),
)
def send_shipping_notification_email(self: Any, order_id: int) -> None:
    """
    Versand Benachrichtigung, ausgelöst von FulfillmentService.update_status()
    beim Übergang nach SHIPPED.
    """
    from apps.orders.models import Order

    order = Order.objects.get(pk=order_id)
    if order.shipping_notification_sent_at is not None:
        # --- bereits versendet (z. B. Retry nach Absturz kurz vor Commit)
        return

    EmailMessage(
        subject=f"Ihre Bestellung {order.order_number} wurde versandt",
        body=render_to_string(
            "orders/emails/shipping_notification.txt",
            {
                "order": order,
                "dashboard_url": f"{settings.FRONTEND_URL}/dashboard",
            },
        ),
        to=[order.email],
    ).send()
    order.shipping_notification_sent_at = timezone.now()
    order.save(update_fields=["shipping_notification_sent_at"])
