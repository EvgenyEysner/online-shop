from adrf import mixins, viewsets
from adrf.mixins import Response, get_data
from asgiref.sync import sync_to_async
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated

from apps.orders.models import Category, Item, Order, OrderItem
from apps.orders.serializers import (
    CartSerializer,
    CategorySerializer,
    ItemSerializer,
    OrderItemSerializer,
    OrderSerializer,
)


class Pagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 300


class CategoryViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = (IsAuthenticated,)
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


class OrderViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = (IsAuthenticated,)
    pagination_class = Pagination
    queryset = Order.objects.select_related("customer").all()
    serializer_class = OrderSerializer


class OrderItemViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = (IsAuthenticated,)
    pagination_class = Pagination
    queryset = OrderItem.objects.select_related("order", "item").all()
    serializer_class = OrderItemSerializer


class CartViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = CartSerializer

    async def acreate(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        await sync_to_async(serializer.is_valid)(raise_exception=True)
        order = await serializer.asave()

        # --- Send mail with order data --- #
        # Todo: Check the celery task
        # order_created.delay(order.id)

        order_data = await get_data(
            OrderSerializer(
                order,
                context=self.get_serializer_context(),
            )
        )
        return Response(order_data, status=status.HTTP_201_CREATED)