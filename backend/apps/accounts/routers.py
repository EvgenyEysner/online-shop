from adrf.routers import DefaultRouter

from .views import PasswordResetViewSet, RegisterViewSet, UserMeViewSet

router = DefaultRouter()

router.register("user", UserMeViewSet, "user")
router.register("sign-up", RegisterViewSet, "sign-up")
router.register("password-reset", PasswordResetViewSet, "password-reset")
