from django.db import transaction

from apps.orders.models import Item, Order, OrderItem


class OrderService:
    @staticmethod
    @transaction.atomic
    def create_order(customer, note, cart_items: list[dict]) -> Order:
        order = Order.objects.create(customer=customer, note=note or "")

        order_items = []
        for entry in cart_items:
            item = entry["item"]
            if not isinstance(item, Item):
                item = Item.objects.get(pk=item)
            order_items.append(
                OrderItem(
                    order=order,
                    item=item,
                    quantity=entry["quantity"],
                )
            )

        OrderItem.objects.bulk_create(order_items)
        return (
            Order.objects.select_related("customer")
            .prefetch_related("items__item")
            .get(pk=order.pk)
        )
