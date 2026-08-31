import stripe
from adrf import mixins, viewsets
from adrf.mixins import Response, get_data
from asgiref.sync import sync_to_async
from django.conf import settings
from django.http import FileResponse
from django_filters import rest_framework as filters
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.throttling import AnonRateThrottle

from apps.orders.exceptions import InsufficientStockError
from apps.orders.models import (
    Category,
    Invoice,
    Item,
    Order,
    OrderItem,
    ReturnRequest,
    Review,
)
from apps.orders.serializers import (
    CategorySerializer,
    CheckoutSessionSerializer,
    InvoiceSerializer,
    ItemSerializer,
    OrderItemSerializer,
    OrderSerializer,
    ReturnRequestSerializer,
    ReviewSerializer,
)
from apps.orders.services.notifications import NotificationService
from apps.orders.services.order import OrderService
from apps.orders.services.order_creation import OrderCreationService
from apps.orders.services.review import ReviewService


class Pagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 300


class CategoryViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = (AllowAny,)
    serializer_class = CategorySerializer
    queryset = Category.objects.all()
    pagination_class = None


class ItemFilter(filters.FilterSet):

    id__in = filters.BaseInFilter(field_name="id")

    class Meta:
        model = Item
        fields = ("id__in",)


class ItemsViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    Nur Lesezugriff über die API. Artikel werden ausschließlich über den
    Django Admin (als Superuser) angelegt, bearbeitet oder gelöscht.
    """

    permission_classes = (AllowAny,)
    parser_classes = (MultiPartParser, FormParser)
    serializer_class = ItemSerializer
    pagination_class = Pagination
    filterset_class = ItemFilter
    queryset = Item.objects.select_related("category").filter(on_stock__gt=0)
    lookup_field = "id"


class OrderViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = (IsAuthenticated,)
    pagination_class = Pagination
    serializer_class = OrderSerializer

    def get_queryset(self):
        return (
            Order.objects.select_related("customer")
            .prefetch_related("items__item")
            .filter(customer=self.request.user)
        )


class OrderItemViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = (IsAuthenticated,)
    pagination_class = Pagination
    serializer_class = OrderItemSerializer

    def get_queryset(self):
        return OrderItem.objects.select_related("order", "item").filter(
            order__customer=self.request.user
        )


class InvoiceViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = (IsAuthenticated,)
    pagination_class = Pagination
    serializer_class = InvoiceSerializer

    def get_queryset(self):
        return Invoice.objects.select_related("order").filter(
            order__customer=self.request.user
        )

    @action(detail=True, methods=["get"])
    def download(self, request, pk=None):
        # get_object() respektiert get_queryset() oben: eine fremde
        # Invoice-ID liefert 404, nie 403 (kein Erraten existierender IDs).
        invoice = self.get_object()
        return FileResponse(
            invoice.pdf_file.open("rb"),
            content_type="application/pdf",
            filename=f"{invoice.invoice_number}.pdf",
            as_attachment=True,
        )


class ReturnRequestViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    Self-Service Rückgabe/Widerruf.
    """

    permission_classes = (IsAuthenticated,)
    pagination_class = Pagination
    serializer_class = ReturnRequestSerializer

    def get_queryset(self):
        return (
            ReturnRequest.objects.select_related("order")
            .prefetch_related("items__order_item")
            .filter(order__customer=self.request.user)
        )


class ReviewViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    Produktbewertungen.
    """

    serializer_class = ReviewSerializer
    pagination_class = Pagination
    filterset_fields = ("item",)

    READ_ONLY_ACTIONS = ("list", "alist", "retrieve", "aretrieve")

    def get_permissions(self):
        if self.action in self.READ_ONLY_ACTIONS:
            self.permission_classes = (AllowAny,)
        else:
            self.permission_classes = (IsAuthenticated,)
        return super().get_permissions()

    def get_queryset(self):
        queryset = Review.objects.select_related("item", "customer")
        if self.action in self.READ_ONLY_ACTIONS:
            return queryset
        return queryset.filter(customer=self.request.user)

    async def perform_adestroy(self, instance):
        await sync_to_async(ReviewService.delete_review)(
            self.request.user, instance.item
        )


class NotificationViewSet(viewsets.GenericViewSet):
    """
    Dashboard-Benachrichtigungsglocke.
    """

    permission_classes = (IsAuthenticated,)

    async def alist(self, request, *args, **kwargs):
        events = await sync_to_async(NotificationService.get_recent_events)(
            request.user
        )
        last_seen = request.user.notifications_last_seen_at

        results = []
        unread_count = 0
        for event in events:
            is_read = last_seen is not None and event.occurred_at <= last_seen
            if not is_read:
                unread_count += 1
            results.append(
                {
                    "kind": event.kind,
                    "order_id": event.order_id,
                    "order_number": event.order_number,
                    "occurred_at": event.occurred_at,
                    "message": event.message,
                    "read": is_read,
                }
            )

        return Response({"results": results, "unread_count": unread_count})


class CheckoutViewSet(viewsets.GenericViewSet):
    permission_classes = (AllowAny,)
    serializer_class = CheckoutSessionSerializer
    throttle_classes = [AnonRateThrottle]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["frontend_url"] = settings.FRONTEND_URL
        return context

    @action(detail=False, methods=["post"], url_path="create-session")
    async def create_session(self, request):
        serializer = self.get_serializer(data=request.data)
        await sync_to_async(serializer.is_valid)(raise_exception=True)
        try:
            result = await sync_to_async(serializer.create_session)()
        except InsufficientStockError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except stripe.error.StripeError as exc:
            return Response(
                {"detail": str(exc.user_message or exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(result, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"], url_path="confirm")
    async def confirm(self, request):
        session_id = request.query_params.get("session_id")
        if not session_id:
            return Response(
                {"detail": "session_id fehlt."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            order = await sync_to_async(OrderService.confirm_session)(session_id)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except stripe.error.StripeError as exc:
            return Response(
                {"detail": str(exc.user_message or exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = await get_data(OrderSerializer(order))
        return Response(data)


class StripeWebhookViewSet(viewsets.GenericViewSet):
    permission_classes = (AllowAny,)
    authentication_classes = []

    @action(detail=False, methods=["post"], url_path="webhook")
    async def webhook(self, request):
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")

        def construct_event():
            return stripe.Webhook.construct_event(
                payload,
                sig_header,
                settings.STRIPE_WEBHOOK_SECRET,
            )

        try:
            event = await sync_to_async(construct_event)()
        except (ValueError, stripe.error.SignatureVerificationError):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if event["type"] in (
            "checkout.session.completed",
            "checkout.session.async_payment_succeeded",
        ):
            session = event["data"]["object"]
            await sync_to_async(OrderService.fulfill_stripe_session)(session)
        elif event["type"] == "checkout.session.async_payment_failed":
            session = event["data"]["object"]

            def mark_failed_and_restock():
                order = Order.objects.filter(stripe_session_id=session["id"]).first()
                if order is None or order.payment_status == Order.PaymentStatus.FAILED:
                    return
                OrderCreationService.restock_order(order)
                order.payment_status = Order.PaymentStatus.FAILED
                order.save(update_fields=["payment_status"])

            await sync_to_async(mark_failed_and_restock)()

        return Response({"received": True})
