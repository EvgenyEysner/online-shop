from typing import Any

from django.contrib import admin, messages
from django.db.models import QuerySet
from django.http import HttpRequest

from .models import (
    Category,
    Invoice,
    Item,
    Order,
    OrderItem,
    ReturnRequest,
    ReturnRequestItem,
    Review,
)
from .services.credit_note import CreditNoteService
from .services.fulfillment import FulfillmentService
from .services.order import OrderService
from .services.returns import ReturnService
from .services.review import ReviewService


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
        "fulfillment_status",
        "total",
        "created_at",
    )
    list_filter = ("payment_status", "fulfillment_status", "payment_method")
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
        "paid_at",
    )
    inlines = [OrderItemInline]

    def save_model(
        self, request: HttpRequest, obj: Order, form: Any, change: bool
    ) -> None:
        """
        payment_status und fulfillment_status bleiben im Admin editierbar
        (Staff kann z. B. eine Überweisung manuell als bezahlt markieren oder
        eine Sendungsnummer erfassen), aber echte Statusübergänge müssen
        wie jeder andere Schreibpfad über die jeweilige zentrale Service-Methode
        laufen, damit Folgeeffekte (paid_at/Rechnung bzw.
        shipped_at/delivered_at/OrderStatusHistory) nicht übergangen werden.

        Beide Übergänge können im selben Admin-Save gleichzeitig auftreten
        (z. B. Zahlung wird bestätigt UND gleichzeitig als versandt
        markiert). Reihenfolge daher bewusst: erst Payment, dann
        Fulfillment, damit FulfillmentService.update_status() bereits den
        aktuellen (ggf. gerade erst gesetzten) payment_status=paid sieht.
        """
        became_paid = False
        fulfillment_changed = False
        new_fulfillment_status = obj.fulfillment_status
        new_tracking_number = obj.tracking_number
        new_carrier = obj.carrier

        if change:
            previous = Order.objects.get(pk=obj.pk)
            became_paid = (
                previous.payment_status != Order.PaymentStatus.PAID
                and obj.payment_status == Order.PaymentStatus.PAID
            )
            fulfillment_changed = previous.fulfillment_status != obj.fulfillment_status

            if became_paid:
                # payment_status dabei unverändert lassen der eigentliche
                # Übergang zu "paid" (inkl. paid_at + Rechnungserstellung +
                # Verlaufs-Eintrag) wird danach kontrolliert über
                # mark_as_paid() vollzogen, statt hier dupliziert zu werden.
                obj.payment_status = previous.payment_status
            if fulfillment_changed:
                # Analog: fulfillment_status/tracking_number/carrier auf den
                # bisherigen Stand zurücksetzen, damit der reguläre Save
                # diesen Übergang nicht unkontrolliert miterledigt -
                # FulfillmentService ist die einzige zulässige Schreibstelle.
                obj.fulfillment_status = previous.fulfillment_status
                obj.tracking_number = previous.tracking_number
                obj.carrier = previous.carrier

        # --- Übrige Feldänderungen (Adresse, Notiz, ...) regulär speichern.
        super().save_model(request, obj, form, change)

        if became_paid:
            OrderService.mark_as_paid(obj, actor=request.user)
        if fulfillment_changed:
            FulfillmentService.update_status(
                obj,
                new_fulfillment_status,
                tracking_number=new_tracking_number,
                carrier=new_carrier,
                actor=request.user,
            )


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    """
    Read-only: Rechnungen sind GoBD-unveränderbar (siehe Invoice.save()/
    delete()-Guards). Staff kann Rechnungen einsehen/erneut herunterladen,
    aber weder bearbeiten noch löschen.
    """

    list_display = (
        "invoice_number",
        "document_type",
        "order",
        "total_amount",
        "issued_at",
        "sent_at",
    )
    list_filter = ("document_type",)
    search_fields = ("invoice_number", "order__order_number", "order__email")
    readonly_fields = tuple(
        field.name for field in Invoice._meta.fields if field.name != "id"
    )
    actions = ("issue_credit_note",)

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False

    @admin.action(description="Rechnung stornieren (Gutschrift erstellen)")
    def issue_credit_note(
        self, request: HttpRequest, queryset: QuerySet[Invoice]
    ) -> None:
        """
        Manuelle Storno-Aktion für Staff-initiierte Stornos ohne vorherige
        ReturnRequest, z. B. bei einem telefonisch
        vereinbarten Storno. Voller Betrag der Ursprungsrechnung, löst
        keinen automatischen Stripe-Refund aus, das ist explizit außerhalb
        des Scopes dieser Aktion.

        Nur auf document_type=invoice Zeilen anwendbar, die noch keine
        credit_notes haben (Doppel-Storno-Schutz).
        """
        eligible = queryset.filter(document_type=Invoice.DocumentType.INVOICE).filter(
            credit_notes__isnull=True
        )
        skipped = queryset.count() - eligible.count()

        created = 0
        for invoice in eligible:
            CreditNoteService.issue_credit_note(
                invoice,
                net_amount=invoice.net_amount,
                tax_amount=invoice.tax_amount,
                total_amount=invoice.total_amount,
                reason="Manueller Storno durch Staff",
                actor=request.user,
            )
            created += 1

        if created:
            self.message_user(
                request,
                f"{created} Gutschrift(en) erstellt.",
                level=messages.SUCCESS,
            )
        if skipped:
            self.message_user(
                request,
                f"{skipped} Rechnung(en) übersprungen (bereits storniert oder "
                "selbst schon eine Gutschrift).",
                level=messages.WARNING,
            )


class ReturnRequestItemInline(admin.TabularInline):
    model = ReturnRequestItem
    extra = 0
    readonly_fields = ("order_item", "quantity")
    can_delete = False


@admin.register(ReturnRequest)
class ReturnRequestAdmin(admin.ModelAdmin):
    """
    Statusübergänge (Genehmigen/Ablehnen/Erstatten) laufen ausschließlich
    über die jeweilige ReturnService-Methode statt über ein rohes
    save() im Admin.

    "Ablehnen" setzt bewusst einen festen, generischen rejection_note Text.
    """

    list_display = (
        "id",
        "order",
        "status",
        "requested_at",
        "decided_at",
        "refunded_at",
    )
    list_filter = ("status",)
    search_fields = ("order__order_number", "order__email")
    readonly_fields = (
        "order",
        "reason",
        "requested_at",
        "decided_at",
        "decided_by",
        "refunded_at",
        "status",
        "rejection_note",
    )
    inlines = (ReturnRequestItemInline,)
    actions = ("approve_returns", "reject_returns", "complete_returns")

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        # Statusfelder sind readonly (s.o.); "Change"-Ansicht bleibt nur zum
        # Einsehen erreichbar, keine Feldänderung per Formular-Save möglich.
        return True

    def has_delete_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False

    @admin.action(description="Genehmigen")
    def approve_returns(
        self, request: HttpRequest, queryset: QuerySet[ReturnRequest]
    ) -> None:
        eligible = queryset.filter(status=ReturnRequest.Status.REQUESTED)
        skipped = queryset.count() - eligible.count()
        approved = 0
        for return_request in eligible:
            ReturnService.approve(return_request, actor=request.user)
            approved += 1

        if approved:
            self.message_user(
                request, f"{approved} Rückgabe(n) genehmigt.", level=messages.SUCCESS
            )
        if skipped:
            self.message_user(
                request,
                f"{skipped} Rückgabe(n) übersprungen (nicht im Status " "'Angefragt').",
                level=messages.WARNING,
            )

    @admin.action(description="Ablehnen")
    def reject_returns(
        self, request: HttpRequest, queryset: QuerySet[ReturnRequest]
    ) -> None:
        eligible = queryset.filter(status=ReturnRequest.Status.REQUESTED)
        skipped = queryset.count() - eligible.count()
        rejected = 0
        for return_request in eligible:
            ReturnService.reject(
                return_request,
                actor=request.user,
                note="Rückgabe abgelehnt. Bei Rückfragen wenden Sie sich "
                "bitte an unseren Kundenservice.",
            )
            rejected += 1

        if rejected:
            self.message_user(
                request, f"{rejected} Rückgabe(n) abgelehnt.", level=messages.SUCCESS
            )
        if skipped:
            self.message_user(
                request,
                f"{skipped} Rückgabe(n) übersprungen (nicht im Status " "'Angefragt').",
                level=messages.WARNING,
            )

    @admin.action(description="Erstatten")
    def complete_returns(
        self, request: HttpRequest, queryset: QuerySet[ReturnRequest]
    ) -> None:
        eligible = queryset.filter(status=ReturnRequest.Status.APPROVED)
        skipped = queryset.count() - eligible.count()
        refunded = 0
        for return_request in eligible:
            ReturnService.complete_return(return_request, actor=request.user)
            refunded += 1

        if refunded:
            self.message_user(
                request, f"{refunded} Rückgabe(n) erstattet.", level=messages.SUCCESS
            )
        if skipped:
            self.message_user(
                request,
                f"{skipped} Rückgabe(n) übersprungen (nicht im Status " "'Genehmigt').",
                level=messages.WARNING,
            )


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):

    list_display = ("item", "customer", "rating", "created_at")
    list_filter = ("rating",)
    search_fields = ("item__name", "customer__email", "customer__first_name")
    readonly_fields = (
        "item",
        "customer",
        "rating",
        "comment",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def delete_queryset(self, request: HttpRequest, queryset: QuerySet[Review]) -> None:
        for review in queryset:
            ReviewService.delete_review(review.customer, review.item)

    def delete_model(self, request: HttpRequest, obj: Review) -> None:
        ReviewService.delete_review(obj.customer, obj.item)
