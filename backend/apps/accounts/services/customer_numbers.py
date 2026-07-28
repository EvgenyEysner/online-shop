"""
Backward-compatible re-export. Prefer apps.accounts.services.identifiers.
"""

from .identifiers import (
    CUSTOMER_NUMBER_KEY,
    CUSTOMER_NUMBER_START,
    SHOP_NUMBER_PREFIX,
    allocate_customer_number,
)

__all__ = [
    "CUSTOMER_NUMBER_KEY",
    "CUSTOMER_NUMBER_START",
    "SHOP_NUMBER_PREFIX",
    "allocate_customer_number",
]
