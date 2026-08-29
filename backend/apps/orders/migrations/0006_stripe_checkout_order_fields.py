import uuid
from decimal import Decimal

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("orders", "0005_alter_category_slug"),
    ]

    operations = [
        migrations.CreateModel(
            name="CheckoutDraft",
            fields=[
                (
                    "id",
                    models.UUIDField(editable=False, primary_key=True, serialize=False),
                ),
                ("payload", models.JSONField()),
                (
                    "stripe_session_id",
                    models.CharField(blank=True, db_index=True, max_length=255),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "Checkout-Entwurf",
                "verbose_name_plural": "Checkout-Entwürfe",
                "ordering": ("-created_at",),
            },
        ),
        migrations.AlterModelOptions(
            name="order",
            options={
                "ordering": ("-created_at",),
                "verbose_name": "Bestellung",
                "verbose_name_plural": "Bestellungen",
            },
        ),
        migrations.AlterModelOptions(
            name="orderitem",
            options={
                "verbose_name": "Bestellposition",
                "verbose_name_plural": "Bestellpositionen",
            },
        ),
        migrations.AddField(
            model_name="order",
            name="billing_city",
            field=models.CharField(blank=True, max_length=128),
        ),
        migrations.AddField(
            model_name="order",
            name="billing_company",
            field=models.CharField(blank=True, max_length=128),
        ),
        migrations.AddField(
            model_name="order",
            name="billing_country",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name="order",
            name="billing_first_name",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name="order",
            name="billing_last_name",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name="order",
            name="billing_salutation",
            field=models.CharField(blank=True, max_length=16),
        ),
        migrations.AddField(
            model_name="order",
            name="billing_same_as_shipping",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="order",
            name="billing_street",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="order",
            name="billing_street_no",
            field=models.CharField(blank=True, max_length=32),
        ),
        migrations.AddField(
            model_name="order",
            name="billing_zip",
            field=models.CharField(blank=True, max_length=16),
        ),
        migrations.AddField(
            model_name="order",
            name="email",
            field=models.EmailField(
                default="guest@example.com", max_length=254, verbose_name="E-Mail"
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="order",
            name="order_number",
            field=models.CharField(
                blank=True, max_length=32, unique=True, verbose_name="Bestellnummer"
            ),
        ),
        migrations.AddField(
            model_name="order",
            name="payment_method",
            field=models.CharField(
                choices=[
                    ("card", "Kreditkarte"),
                    ("paypal", "PayPal"),
                    ("bank", "Überweisung"),
                    ("invoice", "Rechnung"),
                ],
                default="card",
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name="order",
            name="payment_status",
            field=models.CharField(
                choices=[
                    ("pending", "Ausstehend"),
                    ("paid", "Bezahlt"),
                    ("failed", "Fehlgeschlagen"),
                    ("cancelled", "Storniert"),
                ],
                db_index=True,
                default="pending",
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name="order",
            name="phone",
            field=models.CharField(blank=True, max_length=64, verbose_name="Telefon"),
        ),
        migrations.AddField(
            model_name="order",
            name="shipping_city",
            field=models.CharField(default="-", max_length=128),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="order",
            name="shipping_company",
            field=models.CharField(blank=True, max_length=128),
        ),
        migrations.AddField(
            model_name="order",
            name="shipping_country",
            field=models.CharField(default="Deutschland", max_length=64),
        ),
        migrations.AddField(
            model_name="order",
            name="shipping_first_name",
            field=models.CharField(default="Gast", max_length=64),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="order",
            name="shipping_last_name",
            field=models.CharField(default="", max_length=64),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="order",
            name="shipping_salutation",
            field=models.CharField(blank=True, max_length=16),
        ),
        migrations.AddField(
            model_name="order",
            name="shipping_street",
            field=models.CharField(default="-", max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="order",
            name="shipping_street_no",
            field=models.CharField(blank=True, max_length=32),
        ),
        migrations.AddField(
            model_name="order",
            name="shipping_zip",
            field=models.CharField(default="00000", max_length=16),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="order",
            name="shipping_cost",
            field=models.DecimalField(
                decimal_places=2, default=Decimal("0"), max_digits=12
            ),
        ),
        migrations.AddField(
            model_name="order",
            name="stripe_payment_intent_id",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="order",
            name="stripe_session_id",
            field=models.CharField(blank=True, max_length=255, null=True, unique=True),
        ),
        migrations.AddField(
            model_name="order",
            name="subtotal",
            field=models.DecimalField(
                decimal_places=2, default=Decimal("0"), max_digits=12
            ),
        ),
        migrations.AddField(
            model_name="order",
            name="tax_amount",
            field=models.DecimalField(
                decimal_places=2, default=Decimal("0"), max_digits=12
            ),
        ),
        migrations.AddField(
            model_name="order",
            name="total",
            field=models.DecimalField(
                decimal_places=2, default=Decimal("0"), max_digits=12
            ),
        ),
        migrations.AddField(
            model_name="orderitem",
            name="item_name",
            field=models.CharField(default="Artikel", max_length=128),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="orderitem",
            name="unit_price",
            field=models.DecimalField(
                decimal_places=2, default=Decimal("0"), max_digits=10
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="order",
            name="customer",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="orders",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Benutzer",
            ),
        ),
        migrations.AlterField(
            model_name="orderitem",
            name="item",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="order_items",
                to="orders.item",
                verbose_name="Artikel",
            ),
        ),
        migrations.AlterField(
            model_name="orderitem",
            name="quantity",
            field=models.PositiveSmallIntegerField(default=1, verbose_name="Menge"),
        ),
    ]
