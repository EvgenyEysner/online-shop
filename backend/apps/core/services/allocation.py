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
