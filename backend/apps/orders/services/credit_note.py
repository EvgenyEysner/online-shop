import logging
from typing import Any

from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone

from apps.core.services.allocation import NumberAllocationService
from apps.orders.models import Invoice
from apps.orders.services.invoice import InvoiceService
from apps.orders.tasks import send_invoice_email

logger = logging.getLogger(__name__)


class CreditNoteService:
    """
    Einzige zulässige Erzeugungsstelle für Gutschriften/Korrekturrechnungen.
    Aufrufer in diesem Auftrag: die manuelle
    Admin-Aktion "Rechnung stornieren" auf InvoiceAdmin.
    """

    @staticmethod
    @transaction.atomic
    def issue_credit_note(
        invoice: Invoice,
        *,
        net_amount,
        tax_amount,
        total_amount,
        reason: str,
        actor: Any = None,
    ) -> Invoice:
        """
        Erzeugt eine neue Invoice-Zeile mit document_type=CREDIT_NOTE, die
        auf invoice referenziert, rendert das PDF und stößt den E-Mail-Versand an.

        net_amount/tax_amount/total_amount werden vom Aufrufer
        übergeben statt 1:1 von der Ursprungsrechnung übernommen.
        """
        credit_note = Invoice.objects.create(
            order=invoice.order,
            document_type=Invoice.DocumentType.CREDIT_NOTE,
            credited_invoice=invoice,
            reason=reason,
            invoice_number=NumberAllocationService.allocate_credit_note_number(),
            net_amount=net_amount,
            tax_amount=tax_amount,
            total_amount=total_amount,
            tax_rate=invoice.tax_rate,
            service_date=timezone.now().date(),
            buyer_name=invoice.buyer_name,
            buyer_street=invoice.buyer_street,
            buyer_zip=invoice.buyer_zip,
            buyer_city=invoice.buyer_city,
            buyer_country=invoice.buyer_country,
        )
        pdf_bytes = InvoiceService.render_credit_note_pdf(credit_note)
        credit_note.pdf_file.save(
            f"{credit_note.invoice_number}.pdf", ContentFile(pdf_bytes), save=True
        )

        send_invoice_email.delay(credit_note.pk)  # wiederverwendet ADR 0011

        logger.info(
            "Gutschrift %s zu Rechnung %s erstellt (actor=%s, Grund=%r).",
            credit_note.invoice_number,
            invoice.invoice_number,
            actor,
            reason,
        )
        return credit_note
