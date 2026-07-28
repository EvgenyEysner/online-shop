from django.utils import timezone

from apps.accounts.global_identifier import GlobalIdentifier

SHOP_NUMBER_PREFIX = "K39"

CUSTOMER_NUMBER_KEY = "customer_number"
CUSTOMER_NUMBER_START = 100001

ORDER_NUMBER_KEY = "order_number"
ORDER_NUMBER_START = 1000


def allocate_customer_number() -> str:
    """Allocate the next customer number using GlobalIdentifier."""
    sequence = GlobalIdentifier.next(CUSTOMER_NUMBER_KEY, default=CUSTOMER_NUMBER_START)
    return f"{SHOP_NUMBER_PREFIX}-{sequence}"


def allocate_order_number() -> str:
    """Allocate the next order number using GlobalIdentifier."""
    year = timezone.now().year
    sequence = GlobalIdentifier.next(ORDER_NUMBER_KEY, default=ORDER_NUMBER_START)
    return f"{SHOP_NUMBER_PREFIX}-{year}-{sequence:04d}"
