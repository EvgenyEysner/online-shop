from adrf.routers import DefaultRouter

from .views import ItemsViewSet, OrderViewSet, OrderItemViewSet

router = DefaultRouter()

router.register("items", ItemsViewSet, "items")
router.register("orders", OrderViewSet, "orders")
router.register("order-items", OrderItemViewSet, "order-items")
