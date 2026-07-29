from django.db import IntegrityError, transaction
from django.db.models import F

from apps.orders.exceptions import InsufficientStockError
from apps.orders.models import Item, Order, OrderItem
from core.services.allocation import NumberAllocationService
from .pricing import PricingService


class OrderCreationService:
    """
    Erstellt Orders aus einem Checkout-Payload. Idempotent über
    stripe_session_id. Reserviert/erstattet den Lagerbestand atomar passend
    zum Order-Lebenszyklus.
    """

    @staticmethod
    @transaction.atomic
    def create_from_payload(
        *,
        payload: dict,
        stripe_session_id: str,
        stripe_payment_intent_id: str = "",
        customer=None,
        payment_status: str = Order.PaymentStatus.PAID,
    ) -> Order:
        existing = OrderCreationService._get_existing(stripe_session_id)
        if existing:
            return OrderCreationService._update_existing(
                existing,
                payment_status=payment_status,
                stripe_payment_intent_id=stripe_payment_intent_id,
            )

        cart_items = PricingService.resolve_cart_items(payload["items"])
        totals = PricingService.calculate_totals(cart_items)

        # Lagerbestand reservieren, bevor die Order angelegt wird. Schlägt
        # dies fehl, rollt die gesamte Transaktion zurück – es entsteht
        # weder eine Order noch eine verbrauchte Bestellnummer.
        OrderCreationService._reserve_stock(cart_items)

        shipping = payload["shipping"]
        billing = payload.get("billing") or shipping

        try:
            order = Order.objects.create(
                order_number=NumberAllocationService.allocate_order_number(),
                customer=customer,
                email=payload["email"],
                phone=payload.get("phone", ""),
                note=payload.get("note") or "",
                shipping_salutation=shipping.get("salutation", ""),
                shipping_first_name=shipping["first_name"],
                shipping_last_name=shipping["last_name"],
                shipping_company=shipping.get("company", ""),
                shipping_street=shipping["street"],
                shipping_street_no=shipping.get("street_no", ""),
                shipping_zip=shipping["zip"],
                shipping_city=shipping["city"],
                shipping_country=shipping.get("country", "Deutschland"),
                billing_same_as_shipping=bool(
                    payload.get("billing_same_as_shipping", True)
                ),
                billing_salutation=billing.get("salutation", ""),
                billing_first_name=billing.get("first_name", ""),
                billing_last_name=billing.get("last_name", ""),
                billing_company=billing.get("company", ""),
                billing_street=billing.get("street", ""),
                billing_street_no=billing.get("street_no", ""),
                billing_zip=billing.get("zip", ""),
                billing_city=billing.get("city", ""),
                billing_country=billing.get("country", ""),
                payment_method=payload.get("payment_method", Order.PaymentMethod.CARD),
                payment_status=payment_status,
                stripe_session_id=stripe_session_id,
                stripe_payment_intent_id=stripe_payment_intent_id or "",
                subtotal=totals["subtotal"],
                tax_amount=totals["tax_amount"],
                shipping_cost=totals["shipping_cost"],
                total=totals["total"],
            )
        except IntegrityError:
            # Ein paralleler Webhook-Aufruf hat die Order zwischen einem
            # Existenz-Check und .create() bereits angelegt (inkl. eigener
            # Lagerbestands-Reservierung). Unsere Reservierung muss wieder
            # freigegeben werden, sonst würde der Bestand doppelt abgezogen.
            existing = OrderCreationService._get_existing(stripe_session_id)
            OrderCreationService._release_stock(cart_items)
            if existing is None:
                raise
            return OrderCreationService._update_existing(
                existing,
                payment_status=payment_status,
                stripe_payment_intent_id=stripe_payment_intent_id,
            )

        OrderItem.objects.bulk_create(
            [
                OrderItem(
                    order=order,
                    item=entry["item"],
                    item_name=entry["item"].name,
                    unit_price=entry["item"].price,
                    quantity=entry["quantity"],
                )
                for entry in cart_items
            ]
        )

        return OrderCreationService._reload(order.pk)

    @staticmethod
    @transaction.atomic
    def restock_order(order: Order) -> None:
        """
        Gibt den reservierten Lagerbestand einer Order wieder frei (bei
        fehlgeschlagener Zahlung oder Stornierung).
        """
        items = list(order.items.select_related("item").all())
        item_ids = sorted({oi.item_id for oi in items if oi.item_id})
        if not item_ids:
            return

        # Zeilen sperren (feste Reihenfolge, um Deadlocks zu vermeiden),
        # damit der Restock nicht mit einer parallelen Reservierung kollidiert.
        list(Item.objects.select_for_update().filter(pk__in=item_ids))

        for order_item in items:
            if order_item.item_id is None:
                continue  # Artikel wurde inzwischen gelöscht, nichts restockbar
            Item.objects.filter(pk=order_item.item_id).update(
                on_stock=F("on_stock") + order_item.quantity
            )

    @staticmethod
    def _reserve_stock(cart_items: list[dict]) -> None:
        """
        Reduziert den Lagerbestand atomar für alle Cart-Items.
        Sperrt die betroffenen Item-Zeilen (SELECT ... FOR UPDATE)
        in fester Reihenfolge (nach PK sortiert).
        """
        item_ids = sorted({entry["item"].pk for entry in cart_items})
        locked_items = {
            item.pk: item
            for item in Item.objects.select_for_update().filter(pk__in=item_ids)
        }

        for entry in cart_items:
            item = locked_items[entry["item"].pk]
            if entry["quantity"] > item.on_stock:
                raise InsufficientStockError(
                    f"Nur noch {item.on_stock} Stück von '{item.name}' verfügbar."
                )

        for entry in cart_items:
            Item.objects.filter(pk=entry["item"].pk).update(
                on_stock=F("on_stock") - entry["quantity"]
            )

    @staticmethod
    def _release_stock(cart_items: list[dict]) -> None:
        """
        Gibt eine zuvor reservierte Menge wieder frei (Rollback-Pfad).
        """
        for entry in cart_items:
            Item.objects.filter(pk=entry["item"].pk).update(
                on_stock=F("on_stock") + entry["quantity"]
            )

    @staticmethod
    def _get_existing(stripe_session_id: str) -> Order | None:
        return (
            Order.objects.select_related("customer")
            .prefetch_related("items")
            .filter(stripe_session_id=stripe_session_id)
            .first()
        )

    @staticmethod
    def _update_existing(
        order: Order, *, payment_status: str, stripe_payment_intent_id: str
    ) -> Order:
        updates = []
        if (
            payment_status == Order.PaymentStatus.PAID
            and order.payment_status != Order.PaymentStatus.PAID
        ):
            order.payment_status = Order.PaymentStatus.PAID
            updates.append("payment_status")
        if stripe_payment_intent_id and not order.stripe_payment_intent_id:
            order.stripe_payment_intent_id = stripe_payment_intent_id
            updates.append("stripe_payment_intent_id")
        if updates:
            order.save(update_fields=updates)
        return order

    @staticmethod
    def _reload(order_pk) -> Order:
        return (
            Order.objects.select_related("customer")
            .prefetch_related("items__item")
            .get(pk=order_pk)
        )
