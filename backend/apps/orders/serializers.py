from decimal import Decimal
from typing import Any

from adrf import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.relations import PrimaryKeyRelatedField, SlugRelatedField

from apps.orders.models import Category, Item, Order, OrderItem
from apps.orders.services.order import OrderService
from apps.orders.services.pricing import PricingService


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
    item = SlugRelatedField(slug_field="name", read_only=True, allow_null=True)
    line_total = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "item",
            "item_name",
            "unit_price",
            "quantity",
            "line_total",
        ]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "email",
            "phone",
            "note",
            "shipping_salutation",
            "shipping_first_name",
            "shipping_last_name",
            "shipping_company",
            "shipping_street",
            "shipping_street_no",
            "shipping_zip",
            "shipping_city",
            "shipping_country",
            "billing_same_as_shipping",
            "billing_salutation",
            "billing_first_name",
            "billing_last_name",
            "billing_company",
            "billing_street",
            "billing_street_no",
            "billing_zip",
            "billing_city",
            "billing_country",
            "payment_method",
            "payment_status",
            "stripe_session_id",
            "subtotal",
            "tax_amount",
            "shipping_cost",
            "total",
            "items",
            "created_at",
        ]


class AddressSerializer(serializers.Serializer):
    salutation = serializers.CharField(required=False, allow_blank=True, max_length=16)
    first_name = serializers.CharField(max_length=64)
    last_name = serializers.CharField(max_length=64)
    company = serializers.CharField(required=False, allow_blank=True, max_length=128)
    street = serializers.CharField(max_length=255)
    street_no = serializers.CharField(required=False, allow_blank=True, max_length=32)
    zip = serializers.CharField(max_length=16)
    city = serializers.CharField(max_length=128)
    country = serializers.CharField(required=False, allow_blank=True, max_length=64)


class CartItemWriteSerializer(serializers.Serializer):
    item = PrimaryKeyRelatedField(queryset=Item.objects.all())
    quantity = serializers.IntegerField(min_value=1)


class CheckoutSessionSerializer(serializers.Serializer):
    email = serializers.EmailField()
    phone = serializers.CharField(required=False, allow_blank=True, max_length=64)
    note = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, max_length=256
    )
    payment_method = serializers.ChoiceField(choices=Order.PaymentMethod.choices)
    items = CartItemWriteSerializer(many=True)
    shipping = AddressSerializer()
    billing = AddressSerializer(required=False)
    billing_same_as_shipping = serializers.BooleanField(default=True)

    def validate_items(self, value):
        if not value:
            raise ValidationError("Warenkorb darf nicht leer sein.")
        return value

    def validate(self, attrs):
        if not attrs.get("billing_same_as_shipping") and not attrs.get("billing"):
            raise ValidationError({"billing": "Rechnungsadresse ist erforderlich."})
        return attrs

    def create_session(self):
        request = self.context["request"]
        data = self.validated_data
        user = request.user if request.user.is_authenticated else None
        frontend = self.context["frontend_url"].rstrip("/")

        payload: dict[str, Any] = {
            "email": data["email"],
            "phone": data.get("phone", ""),
            "note": data.get("note") or "",
            "payment_method": data["payment_method"],
            "items": data["items"],
            "shipping": data["shipping"],
            "billing": data.get("billing") or data["shipping"],
            "billing_same_as_shipping": data.get("billing_same_as_shipping", True),
        }

        # Validate totals can be computed
        PricingService.calculate_totals(
            PricingService.resolve_cart_items(payload["items"])
        )

        return OrderService.create_checkout_session(
            payload=payload,
            customer=user,
            success_url=f"{frontend}/checkout?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{frontend}/checkout?cancelled=1",
        )
