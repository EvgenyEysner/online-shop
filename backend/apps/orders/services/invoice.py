from typing import TYPE_CHECKING

from django.conf import settings
from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from django.utils import timezone
from weasyprint import HTML

from apps.core.services.allocation import NumberAllocationService

if TYPE_CHECKING:
    from apps.orders.models import Invoice, Order


class InvoiceService:
    """
    Rendert und persistiert das Rechnungs-PDF bei Zahlungseingang.
    Wird ausschließlich von OrderService.mark_as_paid()
    aufgerufen, niemals direkt aus Views.
    """

    @staticmethod
    def ensure_invoice_for_order(order: "Order") -> "Invoice":
        """
        Liefert die bereits vorhandene Original-Rechnung einer
        Order zurück, statt eine zweite zu erzeugen. order.invoices kann
        Gutschriften enthalten, daher wird explizit
        nach document_type=INVOICE gefiltert.
        """
        from apps.orders.models import Invoice

        existing = order.invoices.filter(
            document_type=Invoice.DocumentType.INVOICE
        ).first()
        if existing is not None:
            return existing

        invoice = InvoiceService._create_invoice_row(order)
        pdf_bytes = InvoiceService._render_pdf(invoice, order)
        invoice.pdf_file.save(
            f"{invoice.invoice_number}.pdf",
            ContentFile(pdf_bytes),
            save=True,
        )

        from apps.orders.tasks import send_invoice_email

        send_invoice_email.delay(invoice.pk)

        return invoice

    @staticmethod
    def render_credit_note_pdf(credit_note: "Invoice") -> bytes:
        """
        Rendert das PDF für eine bereits erzeugte Gutschrift Zeile.
        Einzige Erzeugungsstelle für Gutschriften ist
        CreditNoteService.issue_credit_note; diese Methode übernimmt nur
        das Rendering und nutzt dieselbe Vorlage wie die original Rechnung.
        """
        return InvoiceService._render_pdf(credit_note, credit_note.order)

    @staticmethod
    def _create_invoice_row(order: "Order") -> "Invoice":
        from apps.orders.models import Invoice

        buyer = InvoiceService._resolve_buyer_address(order)
        service_date = (order.paid_at or timezone.now()).date()

        return Invoice.objects.create(
            order=order,
            document_type=Invoice.DocumentType.INVOICE,
            invoice_number=NumberAllocationService.allocate_invoice_number(),
            service_date=service_date,
            buyer_name=buyer["name"],
            buyer_street=buyer["street"],
            buyer_zip=buyer["zip"],
            buyer_city=buyer["city"],
            buyer_country=buyer["country"],
            net_amount=order.subtotal,
            tax_rate=settings.TAX_RATE,
            tax_amount=order.tax_amount,
            total_amount=order.total,
        )

    @staticmethod
    def _resolve_buyer_address(order: "Order") -> dict[str, str]:

        use_billing = not order.billing_same_as_shipping and order.billing_street
        prefix = "billing" if use_billing else "shipping"

        first_name = getattr(order, f"{prefix}_first_name")
        last_name = getattr(order, f"{prefix}_last_name")
        company = getattr(order, f"{prefix}_company")
        street = getattr(order, f"{prefix}_street")
        street_no = getattr(order, f"{prefix}_street_no")

        full_name = f"{first_name} {last_name}".strip()
        buyer_name = f"{company}\n{full_name}" if company else full_name
        buyer_street = f"{street} {street_no}".strip()

        return {
            "name": buyer_name,
            "street": buyer_street,
            "zip": getattr(order, f"{prefix}_zip"),
            "city": getattr(order, f"{prefix}_city"),
            "country": getattr(order, f"{prefix}_country"),
        }

    @staticmethod
    def _render_pdf(invoice: "Invoice", order: "Order") -> bytes:
        html = render_to_string(
            "orders/invoice.html",
            {
                "invoice": invoice,
                "order": order,
                "items": order.items.select_related("item").all(),
                "currency": settings.CURRENCY.upper(),
                "company": {
                    "name": settings.COMPANY_NAME,
                    "street": settings.COMPANY_STREET,
                    "zip": settings.COMPANY_ZIP,
                    "city": settings.COMPANY_CITY,
                    "country": settings.COMPANY_COUNTRY,
                    "tax_id": settings.COMPANY_TAX_ID,
                },
            },
        )
        return HTML(string=html).write_pdf()
