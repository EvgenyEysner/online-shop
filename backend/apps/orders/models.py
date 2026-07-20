from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Category(models.Model):
    name = models.CharField("Kategorie", max_length=128)

    def __str__(self):
        return self.name


class Item(models.Model):
    class UnitChoices(models.IntegerChoices):
        PIECES = 1, "Stück"
        METER = 2, "Meter"
        ROLL = 3, "Rolle"

    name = models.CharField("Bezeichnung", max_length=64)
    description = models.TextField(
        "Beschreibung", max_length=256, null=True, blank=True
    )
    image = models.ImageField(
        verbose_name="Artikelbild",
        upload_to="image/items",
        null=True,
        blank=True,
        default="default-product-image.jpg",
    )
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
    unit = models.PositiveSmallIntegerField(
        choices=UnitChoices.choices,
        default=UnitChoices.PIECES,
        verbose_name="Maßeinheit",
    )

    on_stock = models.PositiveSmallIntegerField(verbose_name="Lagerbestand", default=0)
    min_stock = models.PositiveSmallIntegerField(
        verbose_name="Mindestbestand", default=1
    )
    ean = models.CharField(verbose_name="EAN", max_length=13, null=True, blank=True)

    def __str__(self):
        return self.name

    @property
    def tax(self) -> Decimal:
        return self.price * Decimal(0.19)

    class Meta:
        verbose_name = "Artikel"
        verbose_name_plural = "Artikeln"
        ordering = ("name",)


class Order(models.Model):
    customer = models.ForeignKey(
        User, on_delete=models.PROTECT, verbose_name=User._meta.verbose_name
    )

    note = models.TextField(max_length=256, verbose_name="Notiz", blank=True, null=True)

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
        ordering = ("created_at",)

    def __str__(self):
        return f"{self.customer} {self.created_at}"

    def get_total(self):
        return sum(item.quantity for item in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, verbose_name="Auftrag", on_delete=models.CASCADE, related_name="items"
    )
    item = models.ForeignKey(
        Item,
        verbose_name="Artikel",
        on_delete=models.CASCADE,
        related_name="order_items",
    )
    quantity = models.PositiveSmallIntegerField(verbose_name="Menge", default=0)

    class Meta:
        verbose_name = "Artikel"
        verbose_name_plural = "Artikeln"

    def __str__(self):
        return str(self.id)
