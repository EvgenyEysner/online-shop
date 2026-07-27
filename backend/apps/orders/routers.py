from adrf.routers import DefaultRouter

from .views import CartViewSet, ItemsViewSet, OrderItemViewSet, OrderViewSet

router = DefaultRouter()

router.register("items", ItemsViewSet, "items")
router.register("orders", OrderViewSet, "orders")
router.register("order-items", OrderItemViewSet, "order-items")
router.register("cart", CartViewSet, "cart")
