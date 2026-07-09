from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from views import UserMeViewSet

router = DefaultRouter()

router.register("token", TokenObtainPairView, "token")
router.register("refresh", TokenRefreshView, "refresh")
router.register("user", UserMeViewSet, "user")
