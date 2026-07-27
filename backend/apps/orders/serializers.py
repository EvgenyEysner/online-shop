from decimal import Decimal

from adrf import serializers
from asgiref.sync import sync_to_async
from rest_framework.exceptions import ValidationError
from rest_framework.relations import PrimaryKeyRelatedField, SlugRelatedField

from apps.orders.models import Category, Item, Order, OrderItem
from apps.orders.services import OrderService


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "sublabel", "image_url"]


class ItemSerializer(serializers.ModelSerializer):
    tax = serializers.SerializerMethodField(read_only=True)
    category = serializers.SerializerMethodField(read_only=True)
    image = serializers.SerializerMethodField(read_only=True)
    watt = serializers.CharField(source="power_label", read_only=True)

    class Meta:
        model = Item
        fields = [
            "id",
            "name",
            "description",
            "image",
            "manufacturer_number",
            "category",
            "price",
            "original_price",
            "unit",
            "watt",
            "badge",
            "rating",
            "reviews",
            "specs",
            "on_stock",
            "min_stock",
            "ean",
            "tax",
        ]

    async def get_tax(self, obj) -> Decimal:
        return obj.tax

    async def get_category(self, obj) -> str | None:
        if obj.category_id is None:
            return None
        return obj.category.slug

    async def get_image(self, obj) -> str:
        if obj.image_url:
            return obj.image_url
        if obj.image:
            request = self.context.get("request")
            url = obj.image.url
            if request is not None:
                return request.build_absolute_uri(url)
            return url
        return ""


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


class CartItemWriteSerializer(serializers.Serializer):
    item = PrimaryKeyRelatedField(queryset=Item.objects.all())
    quantity = serializers.IntegerField(min_value=1)


class CartSerializer(serializers.Serializer):
    note = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, max_length=256
    )
    items = CartItemWriteSerializer(many=True)

    def validate_items(self, value):
        if not value:
            raise ValidationError("Warenkorb darf nicht leer sein.")
        return value

    async def acreate(self, validated_data):
        request = self.context["request"]
        return await sync_to_async(OrderService.create_order)(
            request.user,
            validated_data.get("note"),
            validated_data["items"],
        )
