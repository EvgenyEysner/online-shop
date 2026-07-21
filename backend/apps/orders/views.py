from adrf import mixins, viewsets
# from drf_spectacular.utils import extend_schema_view, extend_schema
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated

from apps.orders.models import Item, Order, OrderItem
from apps.orders.serializers import ItemSerializer, OrderSerializer, OrderItemSerializer


class Pagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 300


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
