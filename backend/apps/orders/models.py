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
        from django.conf import settings

        return self.price * settings.TAX_RATE

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

    class FulfillmentStatus(models.TextChoices):
        PENDING = "pending", "Ausstehend"
        PROCESSING = "processing", "In Bearbeitung"
        SHIPPED = "shipped", "Versandt"
        DELIVERED = "delivered", "Zugestellt"

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
    paid_at = models.DateTimeField(
        "bezahlt am",
        null=True,
        blank=True,
        editable=False,
        help_text="Zeitpunkt des Zahlungseingangs, gesetzt von "
        "OrderService.mark_as_paid(). Anders als modified_at nicht bei "
        "jedem Save betroffen, daher als Leistungsdatum für Rechnungen "
        "geeignet (§14 Abs. 4 Nr. 6 UStG).",
    )

    fulfillment_status = models.CharField(
        "Versandstatus",
        max_length=16,
        choices=FulfillmentStatus.choices,
        default=FulfillmentStatus.PENDING,
        db_index=True,
    )
    # Freitext statt TextChoices, analog Item.manufacturer_number:
    # unbegrenztes externes Vokabular (beliebige Versanddienstleister),
    # keine feste Geschäfts-Enum wie bei payment_status (siehe ADR 0012).
    carrier = models.CharField(
        "Versanddienstleister", max_length=64, blank=True, default=""
    )
    tracking_number = models.CharField(
        "Sendungsnummer", max_length=128, blank=True, default=""
    )
    shipped_at = models.DateTimeField("versandt am", null=True, blank=True)
    delivered_at = models.DateTimeField("zugestellt am", null=True, blank=True)

    # Transaktions-E-Mails (siehe ADR 0015), Idempotenz-Muster analog
    # Invoice.sent_at.
    confirmation_sent_at = models.DateTimeField(
        "Bestellbestätigung versendet am", null=True, blank=True, editable=False
    )
    shipping_notification_sent_at = models.DateTimeField(
        "Versand-Benachrichtigung versendet am",
        null=True,
        blank=True,
        editable=False,
    )

    class Meta:
        verbose_name = "Bestellung"
        verbose_name_plural = "Bestellungen"
        ordering = ("-created_at",)

    def __str__(self):
        return self.order_number

    def get_total_quantity(self):
        return sum(item.quantity for item in self.items.all())


class OrderStatusHistory(models.Model):
    """
    Audit-Trail jeder Statusänderung einer Order, für beide unabhängigen
    Status-Dimensionen (Zahlung/Versand). Wird ausschließlich von
    OrderService.mark_as_paid() (status_type=PAYMENT) und
    FulfillmentService.update_status() (status_type=FULFILLMENT) befüllt -
    siehe ADR 0012 für die Begründung, warum daneben auch die
    denormalisierten "aktueller Zustand"-Felder auf Order bestehen bleiben.
    """

    class StatusType(models.TextChoices):
        PAYMENT = "payment", "Zahlungsstatus"
        FULFILLMENT = "fulfillment", "Versandstatus"

    order = models.ForeignKey(
        Order,
        verbose_name="Bestellung",
        on_delete=models.CASCADE,
        related_name="status_history",
    )
    status_type = models.CharField(
        "Status-Art", max_length=16, choices=StatusType.choices
    )
    old_value = models.CharField("alter Wert", max_length=32, blank=True, default="")
    new_value = models.CharField("neuer Wert", max_length=32)
    changed_by = models.ForeignKey(
        User,
        verbose_name="geändert von",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        help_text="Staff-Nutzer bei manueller Änderung, None bei "
        "automatischen (z. B. Webhook-getriebenen) Übergängen.",
    )
    note = models.CharField("Notiz", max_length=255, blank=True, default="")
    changed_at = models.DateTimeField("geändert am", auto_now_add=True)

    class Meta:
        verbose_name = "Bestellstatus-Verlauf"
        verbose_name_plural = "Bestellstatus-Verläufe"
        ordering = ("changed_at",)

    def __str__(self) -> str:
        return (
            f"{self.order.order_number}: {self.status_type} "
            f"{self.old_value} → {self.new_value}"
        )


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
        ordering = ("order_id",)

    def __str__(self):
        return f"{self.item_name} × {self.quantity}"

    @property
    def line_total(self) -> Decimal:
        return self.unit_price * self.quantity


class Invoice(models.Model):
    """
    Rechnung bzw. Gutschrift/Korrekturrechnung zu einer Order.
    GoBD-Unveränderbarkeit (§147 AO): Nach der initialen Erstellung dürfen
    die rechnungsrelevanten Felder nicht mehr verändert werden, +siehe
    save(). Einzige zulässige Nachtrags-Aktualisierung ist sent_at
    (Versandbestätigung berührt keinen rechnungsrelevanten Inhalt).

    order ist ForeignKey, da eine Order sowohl eine Original Rechnung
    als auch im Storno Fall eine Korrekturrechnung als jeweils eigene
    Invoice Zeile besitzen kann.
    """

    class DocumentType(models.TextChoices):
        INVOICE = "invoice", "Rechnung"
        CREDIT_NOTE = "credit_note", "Gutschrift/Korrekturrechnung"

    order = models.ForeignKey(
        Order,
        verbose_name="Bestellung",
        on_delete=models.PROTECT,
        related_name="invoices",
    )
    document_type = models.CharField(
        "Dokumenttyp",
        max_length=16,
        choices=DocumentType.choices,
        default=DocumentType.INVOICE,
    )
    credited_invoice = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="credit_notes",
        verbose_name="korrigierte Rechnung",
        help_text="Nur gesetzt bei document_type=credit_note: referenzierte "
        "Ursprungsrechnung.",
    )
    reason = models.CharField("Grund", max_length=255, blank=True, default="")

    invoice_number = models.CharField(
        "Rechnungsnummer", max_length=32, unique=True, editable=False
    )
    issued_at = models.DateTimeField(
        "ausgestellt am", auto_now_add=True, editable=False
    )
    service_date = models.DateField(
        "Leistungsdatum",
        editable=False,
        help_text="Tag der Vereinnahmung des Entgelts (§14 Abs. 4 Nr. 6 "
        "UStG), da Zahlung vor Lieferung erfolgt.",
    )
    buyer_name = models.CharField("Käufer", max_length=160, editable=False)
    buyer_street = models.CharField("Käufer Straße", max_length=255, editable=False)
    buyer_zip = models.CharField("Käufer PLZ", max_length=16, editable=False)
    buyer_city = models.CharField("Käufer Ort", max_length=128, editable=False)
    buyer_country = models.CharField("Käufer Land", max_length=64, editable=False)

    net_amount = models.DecimalField(
        "Nettobetrag", max_digits=12, decimal_places=2, editable=False
    )
    tax_rate = models.DecimalField(
        "Steuersatz", max_digits=4, decimal_places=3, editable=False
    )
    tax_amount = models.DecimalField(
        "Steuerbetrag", max_digits=12, decimal_places=2, editable=False
    )
    total_amount = models.DecimalField(
        "Gesamtbetrag", max_digits=12, decimal_places=2, editable=False
    )

    pdf_file = models.FileField("PDF-Datei", upload_to="invoices/%Y/", editable=False)
    sent_at = models.DateTimeField(
        "versendet am", null=True, blank=True, editable=False
    )

    class Meta:
        verbose_name = "Rechnung"
        verbose_name_plural = "Rechnungen"
        ordering = ("-issued_at",)

    def __str__(self) -> str:
        return self.invoice_number

    @property
    def tax_rate_percent(self) -> Decimal:
        return self.tax_rate * Decimal("100")

    def save(self, *args, **kwargs):
        # GoBD: nach Erstellung unveränderbar. sent_at ist die einzige
        # zulässige Nachtrags-Aktualisierung.
        #
        # Ein reiner != Vergleich zweier
        # FieldFil Objekte (pdf_file) wäre über Identität, nicht Wert,
        # implementiert (Django definiert dafür kein `__eq__`) und würde
        # bei *jedem* Save fälschlich "geändert" melden. Zusätzlich wird
        # `pdf_file` von InvoiceService bewusst erst in einem zweiten
        # Save-Aufruf befüllt (Dateiname enthält die erst beim Insert
        # feststehende invoice_number) ein reiner Wertvergleich hätte
        # diesen leer -> belegt Übergang ebenfalls fälschlich blockiert. Beide
        # Fälle werden hier durch (a) einen Vergleich über `.name` statt
        # Objektidentität und (b) das Zulassen von leer->belegt-Übergängen
        # (= Vervollständigung der initialen Erstellung) behoben, ohne die
        # eigentliche Absicht des Guards (keine Änderung nach Erstellung)
        # aufzuweichen.
        if self.pk is not None:
            original = Invoice.objects.get(pk=self.pk)
            protected = {
                f.name for f in self._meta.fields if f.name not in ("id", "sent_at")
            }
            changed = set()
            for field_name in protected:
                old_value = getattr(original, field_name)
                new_value = getattr(self, field_name)
                if hasattr(old_value, "name") and hasattr(new_value, "name"):
                    # FileField: Wertvergleich über den Speicherpfad statt
                    # über FieldFile-Objektidentität (siehe oben).
                    old_value = old_value.name or ""
                    new_value = new_value.name or ""
                if not old_value and new_value:
                    continue  # Vervollständigung der initialen Erstellung
                if old_value != new_value:
                    changed.add(field_name)
            if changed:
                raise ValueError(
                    f"Invoice ist unveränderbar (GoBD), Felder betroffen: {changed}"
                )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError(
            "Invoice darf laut GoBD-Aufbewahrungspflicht nicht gelöscht werden."
        )


class ReturnRequest(models.Model):
    """
    Self-Service Rückgabe/Widerruf einer Order. Eigene
    Entität statt eines dritten Statusfelds auf Order (analog zur
    Begründung für Invoice/OrderStatusHistory), da der Vorgang granularer
    (Item-/Mengen genau, siehe ReturnRequestItem) und mehrstufig ist
    (REQUESTED -> APPROVED -> REFUNDED bzw. REJECTED), mit eigenen
    Zeitstempeln/Entscheidern.
    """

    class Status(models.TextChoices):
        REQUESTED = "requested", "Angefragt"
        APPROVED = "approved", "Genehmigt"
        REJECTED = "rejected", "Abgelehnt"
        REFUNDED = "refunded", "Erstattet"

    order = models.ForeignKey(
        Order,
        verbose_name="Bestellung",
        on_delete=models.PROTECT,
        related_name="return_requests",
    )
    status = models.CharField(
        "Status",
        max_length=16,
        choices=Status.choices,
        default=Status.REQUESTED,
        db_index=True,
    )
    reason = models.TextField("Grund", max_length=500)
    requested_at = models.DateTimeField("angefragt am", auto_now_add=True)
    decided_at = models.DateTimeField("entschieden am", null=True, blank=True)
    decided_by = models.ForeignKey(
        User,
        verbose_name="entschieden von",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    rejection_note = models.CharField(
        "Ablehnungsgrund", max_length=255, blank=True, default=""
    )
    refunded_at = models.DateTimeField("erstattet am", null=True, blank=True)

    class Meta:
        verbose_name = "Rückgabeanfrage"
        verbose_name_plural = "Rückgabeanfragen"
        ordering = ("-requested_at",)

    def __str__(self) -> str:
        return f"Rückgabe #{self.pk} zu {self.order.order_number}"


class ReturnRequestItem(models.Model):
    """
    Einzelposition einer ReturnRequest
    """

    return_request = models.ForeignKey(
        ReturnRequest,
        verbose_name="Rückgabeanfrage",
        on_delete=models.CASCADE,
        related_name="items",
    )
    order_item = models.ForeignKey(
        OrderItem,
        verbose_name="Bestellposition",
        on_delete=models.PROTECT,
        related_name="+",
    )
    quantity = models.PositiveSmallIntegerField("Menge")

    class Meta:
        verbose_name = "Rückgabeposition"
        verbose_name_plural = "Rückgabepositionen"
        ordering = ("return_request_id",)

    def __str__(self) -> str:
        return f"{self.order_item.item_name} x{self.quantity}"


class Review(models.Model):
    """
    Produktbewertung eines verifizierten Käufers.
    """

    item = models.ForeignKey(
        Item,
        verbose_name="Artikel",
        on_delete=models.CASCADE,
        related_name="product_reviews",
    )
    customer = models.ForeignKey(
        User,
        verbose_name=User._meta.verbose_name,
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    rating = models.PositiveSmallIntegerField(
        "Bewertung", choices=[(i, str(i)) for i in range(1, 6)]
    )
    comment = models.TextField("Kommentar", max_length=1000, blank=True, default="")
    created_at = models.DateTimeField("erstellt am", auto_now_add=True)
    updated_at = models.DateTimeField("geändert am", auto_now=True)

    class Meta:
        verbose_name = "Bewertung"
        verbose_name_plural = "Bewertungen"
        ordering = ("-created_at",)
        constraints = (
            models.UniqueConstraint(
                fields=["item", "customer"], name="unique_review_per_customer_item"
            ),
        )

    def __str__(self) -> str:
        return f"{self.customer.full_name}: {self.item.name} ({self.rating}/5)"
