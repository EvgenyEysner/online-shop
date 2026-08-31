from adrf.routers import DefaultRouter

from .views import (
    CategoryViewSet,
    CheckoutViewSet,
    InvoiceViewSet,
    ItemsViewSet,
    NotificationViewSet,
    OrderItemViewSet,
    OrderViewSet,
    ReturnRequestViewSet,
    ReviewViewSet,
    StripeWebhookViewSet,
)

router = DefaultRouter()

router.register("categories", CategoryViewSet, basename="categories")
router.register("items", ItemsViewSet, basename="items")
router.register("orders", OrderViewSet, basename="orders")
router.register("order-items", OrderItemViewSet, basename="order-items")
router.register("invoices", InvoiceViewSet, basename="invoice")
router.register("return-requests", ReturnRequestViewSet, basename="return-request")
router.register("reviews", ReviewViewSet, basename="review")
router.register("notifications", NotificationViewSet, basename="notification")
router.register("checkout", CheckoutViewSet, basename="checkout")
router.register("stripe", StripeWebhookViewSet, basename="stripe")
