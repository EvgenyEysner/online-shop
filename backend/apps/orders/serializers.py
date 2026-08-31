from decimal import Decimal
from typing import Any

from adrf import serializers
from asgiref.sync import sync_to_async
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError
from rest_framework.relations import PrimaryKeyRelatedField, SlugRelatedField

from apps.orders.exceptions import InsufficientStockError
from apps.orders.models import (
    Category,
    Invoice,
    Item,
    Order,
    OrderItem,
    ReturnRequest,
    ReturnRequestItem,
    Review,
)
from apps.orders.services.order import OrderService
from apps.orders.services.pricing import PricingService
from apps.orders.services.returns import ReturnService
from apps.orders.services.review import ReviewService


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
    # Zusätzlich zum Namen (item) auch die rohe Artikel-ID, damit das
    # Frontend gezielt die aktuellen Artikeldaten nachladen kann (siehe
    # ADR 0020, "Erneut bestellen") - additiv, item bleibt unverändert.
    item_id = PrimaryKeyRelatedField(source="item", read_only=True)
    line_total = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "item",
            "item_id",
            "item_name",
            "unit_price",
            "quantity",
            "line_total",
        ]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    has_invoice = serializers.SerializerMethodField(read_only=True)
    can_request_return = serializers.SerializerMethodField(read_only=True)

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
            "subtotal",
            "tax_amount",
            "shipping_cost",
            "total",
            "items",
            "created_at",
            "paid_at",
            "fulfillment_status",
            "tracking_number",
            "carrier",
            "shipped_at",
            "delivered_at",
            "has_invoice",
            "can_request_return",
        ]

    async def get_has_invoice(self, obj) -> bool:
        return await Invoice.objects.filter(order=obj).aexists()

    async def get_can_request_return(self, obj) -> bool:
        return ReturnService.can_request_return(obj)


class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = [  # noqa: RUF012 - Meta.fields ist projektweit unannotiert
            "id",
            "invoice_number",
            "document_type",
            "issued_at",
            "net_amount",
            "tax_rate",
            "tax_amount",
            "total_amount",
            "sent_at",
            "order",
        ]


class ReviewSerializer(serializers.ModelSerializer):

    customer = SlugRelatedField(slug_field="full_name", read_only=True)
    customer_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Review
        fields = (
            "id",
            "item",
            "customer",
            "customer_id",
            "rating",
            "comment",
            "created_at",
            "updated_at",
        )

    async def acreate(self, validated_data):
        request = self.context["request"]
        return await sync_to_async(ReviewService.upsert_review)(
            request.user,
            validated_data["item"],
            rating=validated_data["rating"],
            comment=validated_data.get("comment", ""),
        )

    async def aupdate(self, instance, validated_data):
        request = self.context["request"]
        return await sync_to_async(ReviewService.upsert_review)(
            request.user,
            instance.item,
            rating=validated_data.get("rating", instance.rating),
            comment=validated_data.get("comment", instance.comment),
        )


class ReturnRequestItemSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source="order_item.item_name", read_only=True)

    class Meta:
        model = ReturnRequestItem
        fields = ("id", "order_item", "item_name", "quantity")


class ReturnRequestSerializer(serializers.ModelSerializer):

    items = ReturnRequestItemSerializer(many=True)

    class Meta:
        model = ReturnRequest
        fields = (
            "id",
            "order",
            "status",
            "reason",
            "requested_at",
            "decided_at",
            "rejection_note",
            "refunded_at",
            "items",
        )
        extra_kwargs = {  # noqa: RUF012 - von DRF vorgegebene Struktur
            "status": {"read_only": True},
            "requested_at": {"read_only": True},
            "decided_at": {"read_only": True},
            "rejection_note": {"read_only": True},
            "refunded_at": {"read_only": True},
        }

    def validate(self, attrs):
        request = self.context["request"]
        order = attrs["order"]
        if order.customer_id != request.user.id:
            raise ValidationError(
                {"order": "Diese Bestellung gehört nicht zu Ihrem Konto."}
            )

        items = attrs.get("items") or []
        if not items:
            raise ValidationError(
                {"items": "Mindestens eine Rückgabeposition ist erforderlich."}
            )
        for entry in items:
            order_item = entry["order_item"]
            if order_item.order_id != order.id:
                raise ValidationError(
                    {
                        "items": f"Bestellposition {order_item.pk} gehört nicht "
                        "zu dieser Bestellung."
                    }
                )

        return attrs

    async def acreate(self, validated_data):
        order = validated_data["order"]
        items = validated_data["items"]
        reason = validated_data.get("reason", "")
        try:
            return await sync_to_async(ReturnService.create_request)(
                order, items=items, reason=reason
            )
        except DjangoValidationError as exc:
            raise ValidationError({"detail": exc.messages}) from exc


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
    item = PrimaryKeyRelatedField(queryset=Item.objects.filter(on_stock__gt=0))
    quantity = serializers.IntegerField(min_value=1)

    def validate(self, attrs):
        item = attrs["item"]
        quantity = attrs["quantity"]
        if quantity > item.on_stock:
            raise ValidationError(
                {
                    "quantity": f"Nur noch {item.on_stock} Stück von '{item.name}' verfügbar."
                }
            )
        return attrs


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

        try:
            PricingService.calculate_totals(
                PricingService.resolve_cart_items(attrs["items"])
            )
        except Item.DoesNotExist:
            raise ValidationError(
                {"items": "Ein oder mehrere Artikel sind nicht mehr verfügbar."}
            )
        except InsufficientStockError as exc:
            raise ValidationError({"items": str(exc)})

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

        return OrderService.create_checkout_session(
            payload=payload,
            customer=user,
            success_url=f"{frontend}/checkout?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{frontend}/checkout?cancelled=1",
        )
