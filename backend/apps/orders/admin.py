from django.contrib import admin

from .models import Category, CheckoutDraft, Item, Order, OrderItem  # noqa: F401


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "sublabel")
    search_fields = ("name", "slug")


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "on_stock", "min_stock", "ean")
    list_filter = ("category", "unit")
    search_fields = ("name", "manufacturer_number", "ean")


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("item", "item_name", "unit_price", "quantity", "line_total")
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_number",
        "email",
        "payment_method",
        "payment_status",
        "total",
        "created_at",
    )
    list_filter = ("payment_status", "payment_method")
    search_fields = ("order_number", "email", "stripe_session_id")
    readonly_fields = (
        "stripe_session_id",
        "stripe_payment_intent_id",
        "subtotal",
        "tax_amount",
        "shipping_cost",
        "total",
        "created_at",
        "modified_at",
    )
    inlines = [OrderItemInline]
