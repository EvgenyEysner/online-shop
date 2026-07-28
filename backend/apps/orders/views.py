from adrf import mixins, viewsets
from adrf.mixins import Response, get_data
from asgiref.sync import sync_to_async
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
import stripe

from apps.orders.models import Category, Item, Order, OrderItem
from apps.orders.serializers import (
    CategorySerializer,
    CheckoutSessionSerializer,
    ItemSerializer,
    OrderItemSerializer,
    OrderSerializer,
)
from apps.orders.services import OrderService


class Pagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 300


class CategoryViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = (AllowAny,)
    serializer_class = CategorySerializer
    queryset = Category.objects.all()
    pagination_class = None


class ItemsViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = (IsAuthenticated,)
    parser_classes = (MultiPartParser, FormParser)
    serializer_class = ItemSerializer
    pagination_class = Pagination
    queryset = Item.objects.select_related("category").all()
    lookup_field = "id"

    def get_permissions(self):
        if self.action in ("list", "retrieve", "alist", "aretrieve"):
            return [AllowAny()]
        return [IsAuthenticated()]


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
    queryset = OrderItem.objects.select_related("order", "item").all()
    serializer_class = OrderItemSerializer


class CheckoutViewSet(viewsets.GenericViewSet):
    permission_classes = (AllowAny,)
    serializer_class = CheckoutSessionSerializer

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

            def mark_failed():
                Order.objects.filter(stripe_session_id=session["id"]).update(
                    payment_status=Order.PaymentStatus.FAILED
                )

            await sync_to_async(mark_failed)()

        return Response({"received": True})
