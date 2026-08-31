from django.conf import settings
from django.utils import timezone

from apps.core.models import GlobalIdentifier


class NumberAllocationService:
    """Vergabe fortlaufender Nummern (Kunden, Bestellungen, ...)."""

    @classmethod
    def _prefix(cls) -> str:
        return settings.SHOP_NUMBER_PREFIX

    @classmethod
    def allocate_customer_number(cls) -> str:
        """Vergibt die nächste Kundennummer."""
        sequence = GlobalIdentifier.next(
            settings.CUSTOMER_NUMBER_KEY, default=settings.CUSTOMER_NUMBER_START
        )
        return f"{cls._prefix()}-{sequence}"

    @classmethod
    def allocate_order_number(cls) -> str:
        """Vergibt die nächste Bestellnummer für das aktuelle Jahr."""
        year = timezone.now().year
        key = f"{settings.ORDER_NUMBER_KEY}_{year}"
        sequence = GlobalIdentifier.next(key, default=settings.ORDER_NUMBER_START)
        return f"{cls._prefix()}-{year}-{sequence:04d}"

    @classmethod
    def allocate_invoice_number(cls) -> str:
        """
        Vergibt die nächste Rechnungsnummer für das aktuelle Jahr.
        """
        year = timezone.now().year
        key = f"{settings.INVOICE_NUMBER_KEY}_{year}"
        sequence = GlobalIdentifier.next(key, default=settings.INVOICE_NUMBER_START)
        return f"RE-{year}-{sequence:04d}"

    @classmethod
    def allocate_credit_note_number(cls) -> str:
        """
        Vergibt die nächste Gutschrift-/Korrekturrechnungsnummer für das
        aktuelle Jahr. Eigene Sequenz statt Wiederverwendung der
        Rechnungsnummern-Sequenz (siehe ADR 0016, gleiche Begründung wie
        getrennte Zähler in ADR 0009).
        """
        year = timezone.now().year
        key = f"{settings.CREDIT_NOTE_NUMBER_KEY}_{year}"
        sequence = GlobalIdentifier.next(key, default=settings.CREDIT_NOTE_NUMBER_START)
        return f"GS-{year}-{sequence:04d}"
