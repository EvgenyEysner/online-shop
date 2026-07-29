from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings

from apps.orders.exceptions import InsufficientStockError
from apps.orders.models import Item


class PricingService:
    """
    Warenkorb-Auflösung und Preis-/Steuerberechnung.
    """

    @staticmethod
    def money(value: Decimal) -> Decimal:
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @classmethod
    def resolve_cart_items(cls, raw_items: list[dict]) -> list[dict]:
        """
        Löst Item-Referenzen (PK oder Instanz) zu Item-Objekten auf.
        Holt alle fehlenden Items in einer einzigen Query.

        Prüft die Menge gegen den zum Abfragezeitpunkt gelesenen Bestand
        (ungesperrt) – dient als frühes UX-Feedback (z. B. 400 statt eine
        Stripe-Session zu erzeugen). Die verbindliche, gesperrte Prüfung
        passiert erst in OrderCreationService._reserve_stock() beim
        tatsächlichen Anlegen der Order.
        """
        missing_ids = [
            entry["item"] for entry in raw_items if not isinstance(entry["item"], Item)
        ]
        items_by_id = Item.objects.in_bulk(missing_ids) if missing_ids else {}

        resolved = []
        for entry in raw_items:
            item = entry["item"]
            quantity = int(entry["quantity"])

            if not isinstance(item, Item):
                try:
                    item = items_by_id[item]
                except KeyError:
                    raise Item.DoesNotExist(f"Item {item!r} nicht gefunden.") from None

            if quantity > item.on_stock:
                raise InsufficientStockError(
                    f"Nur noch {item.on_stock} Stück von '{item.name}' verfügbar."
                )

            resolved.append({"item": item, "quantity": quantity})
        return resolved

    @classmethod
    def calculate_totals(cls, cart_items: list[dict]) -> dict[str, Decimal]:
        subtotal = sum(
            (
                cls.money(entry["item"].price * entry["quantity"])
                for entry in cart_items
            ),
            Decimal("0.00"),
        )
        shipping = (
            Decimal("0.00")
            if subtotal >= settings.FREE_SHIPPING_THRESHOLD
            else settings.SHIPPING_COST
        )
        tax_amount = cls.money(subtotal * settings.TAX_RATE)
        total = cls.money(subtotal + tax_amount + shipping)
        return {
            "subtotal": subtotal,
            "tax_amount": tax_amount,
            "shipping_cost": cls.money(shipping),
            "total": total,
        }
