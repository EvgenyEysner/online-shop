from adrf.routers import DefaultRouter

from .views import (
    CategoryViewSet,
    CheckoutViewSet,
    ItemsViewSet,
    OrderItemViewSet,
    OrderViewSet,
    StripeWebhookViewSet,
)

router = DefaultRouter()

router.register("categories", CategoryViewSet, basename="categories")
router.register("items", ItemsViewSet, basename="items")
router.register("orders", OrderViewSet, basename="orders")
router.register("order-items", OrderItemViewSet, basename="order-items")
router.register("checkout", CheckoutViewSet, basename="checkout")
router.register("stripe", StripeWebhookViewSet, basename="stripe")
