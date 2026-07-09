from rest_framework.routers import DefaultRouter

from .views import UserMeViewSet

router = DefaultRouter()

router.register("user", UserMeViewSet, "user")
