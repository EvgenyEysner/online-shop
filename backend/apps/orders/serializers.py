from decimal import Decimal

from adrf import serializers
from rest_framework.relations import SlugRelatedField

from apps.orders.models import Category, Item, Order, OrderItem


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


class ItemSerializer(serializers.ModelSerializer):
    tax = serializers.SerializerMethodField(read_only=True)
    category = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Item
        fields = [
            "name",
            "description",
            "image",
            "manufacturer_number",
            "category",
            "price",
            "unit",
            "on_stock",
            "min_stock",
            "ean",
            "tax",
        ]

    def get_tax(self, obj) -> Decimal:
        return obj.tax

    def get_category(self, obj) -> str | None:
        if obj.category_id is None:
            return None
        return obj.category.name


class OrderItemSerializer(serializers.ModelSerializer):
    item = SlugRelatedField(slug_field="name", read_only=True)

    class Meta:
        model = OrderItem
        fields = "__all__"


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    customer = SlugRelatedField(slug_field="last_name", read_only=True)

    class Meta:
        model = Order
        fields = "__all__"
