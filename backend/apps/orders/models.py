from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Category(models.Model):
    name = models.CharField("Kategorie", max_length=128)
    slug = models.SlugField("Schlüssel", max_length=64, unique=True)
    sublabel = models.CharField("Untertitel", max_length=128, blank=True)
    image_url = models.URLField("Bild-URL", blank=True)

    class Meta:
        verbose_name = "Kategorie"
        verbose_name_plural = "Kategorien"
        ordering = ("name",)

    def __str__(self):
        return self.name


class Item(models.Model):
    class UnitChoices(models.IntegerChoices):
        PIECES = 1, "Stück"
        METER = 2, "Meter"
        ROLL = 3, "Rolle"

    name = models.CharField("Bezeichnung", max_length=128)
    description = models.TextField(
        "Beschreibung", max_length=512, null=True, blank=True
    )
    image = models.ImageField(
        verbose_name="Artikelbild",
        upload_to="image/items",
        null=True,
        blank=True,
        default="default-product-image.jpg",
    )
    image_url = models.URLField("Externe Bild-URL", blank=True)
    manufacturer_number = models.CharField(
        "Hersteller Artikelnummer", max_length=64, blank=True
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="products",
        null=True,
        blank=True,
        verbose_name="Kategorie",
    )
    price = models.DecimalField("Preis", max_digits=10, decimal_places=2)
    original_price = models.DecimalField(
        "UVP / Streichpreis",
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )
    unit = models.PositiveSmallIntegerField(
        choices=UnitChoices.choices,
        default=UnitChoices.PIECES,
        verbose_name="Maßeinheit",
    )
    power_label = models.CharField("Leistung / Kennwert", max_length=64, blank=True)
    badge = models.CharField("Badge", max_length=64, blank=True)
    rating = models.DecimalField(
        "Bewertung", max_digits=2, decimal_places=1, default=Decimal("0.0")
    )
    reviews = models.PositiveIntegerField("Anzahl Bewertungen", default=0)
    specs = models.JSONField("Technische Daten", default=list, blank=True)

    on_stock = models.PositiveSmallIntegerField(verbose_name="Lagerbestand", default=0)
    min_stock = models.PositiveSmallIntegerField(
        verbose_name="Mindestbestand", default=1
    )
    ean = models.CharField(verbose_name="EAN", max_length=13, null=True, blank=True)

    def __str__(self):
        return self.name

    @property
    def tax(self) -> Decimal:
        return self.price * Decimal("0.19")

    class Meta:
        verbose_name = "Artikel"
        verbose_name_plural = "Artikeln"
        ordering = ("name",)


class CheckoutDraft(models.Model):
    """Temporary cart + address payload until Stripe payment succeeds."""

    id = models.UUIDField(primary_key=True, editable=False)
    payload = models.JSONField()
    stripe_session_id = models.CharField(max_length=255, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Checkout-Entwurf"
        verbose_name_plural = "Checkout-Entwürfe"
        ordering = ("-created_at",)

    def __str__(self):
        return str(self.id)


class Order(models.Model):
    class PaymentStatus(models.TextChoices):
        PENDING = "pending", "Ausstehend"
        PAID = "paid", "Bezahlt"
        FAILED = "failed", "Fehlgeschlagen"
        CANCELLED = "cancelled", "Storniert"

    class PaymentMethod(models.TextChoices):
        CARD = "card", "Kreditkarte"
        PAYPAL = "paypal", "PayPal"
        BANK = "bank", "Überweisung"
        INVOICE = "invoice", "Rechnung"

    order_number = models.CharField(
        "Bestellnummer", max_length=32, unique=True, blank=True
    )
    customer = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        verbose_name=User._meta.verbose_name,
        null=True,
        blank=True,
        related_name="orders",
    )
    email = models.EmailField("E-Mail")
    phone = models.CharField("Telefon", max_length=64, blank=True)
    note = models.TextField(max_length=256, verbose_name="Notiz", blank=True, null=True)

    # Shipping
    shipping_salutation = models.CharField(max_length=16, blank=True)
    shipping_first_name = models.CharField(max_length=64)
    shipping_last_name = models.CharField(max_length=64)
    shipping_company = models.CharField(max_length=128, blank=True)
    shipping_street = models.CharField(max_length=255)
    shipping_street_no = models.CharField(max_length=32, blank=True)
    shipping_zip = models.CharField(max_length=16)
    shipping_city = models.CharField(max_length=128)
    shipping_country = models.CharField(max_length=64, default="Deutschland")

    # Billing
    billing_same_as_shipping = models.BooleanField(default=True)
    billing_salutation = models.CharField(max_length=16, blank=True)
    billing_first_name = models.CharField(max_length=64, blank=True)
    billing_last_name = models.CharField(max_length=64, blank=True)
    billing_company = models.CharField(max_length=128, blank=True)
    billing_street = models.CharField(max_length=255, blank=True)
    billing_street_no = models.CharField(max_length=32, blank=True)
    billing_zip = models.CharField(max_length=16, blank=True)
    billing_city = models.CharField(max_length=128, blank=True)
    billing_country = models.CharField(max_length=64, blank=True)

    payment_method = models.CharField(
        max_length=16, choices=PaymentMethod.choices, default=PaymentMethod.CARD
    )
    payment_status = models.CharField(
        max_length=16,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        db_index=True,
    )
    stripe_session_id = models.CharField(max_length=255, unique=True, db_index=True)
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True)

    subtotal = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0")
    )
    tax_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0")
    )
    shipping_cost = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0")
    )
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="erstellt am",
        editable=False,
    )
    modified_at = models.DateTimeField(
        verbose_name="geändert am", editable=False, auto_now=True
    )

    class Meta:
        verbose_name = "Bestellung"
        verbose_name_plural = "Bestellungen"
        ordering = ("-created_at",)

    def __str__(self):
        return self.order_number

    def get_total_quantity(self):
        return sum(item.quantity for item in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, verbose_name="Auftrag", on_delete=models.CASCADE, related_name="items"
    )
    item = models.ForeignKey(
        Item,
        verbose_name="Artikel",
        on_delete=models.PROTECT,
        related_name="order_items",
        null=True,
        blank=True,
    )
    item_name = models.CharField(max_length=128)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveSmallIntegerField(verbose_name="Menge", default=1)

    class Meta:
        verbose_name = "Bestellposition"
        verbose_name_plural = "Bestellpositionen"

    def __str__(self):
        return f"{self.item_name} × {self.quantity}"

    @property
    def line_total(self) -> Decimal:
        return self.unit_price * self.quantity
