from adrf import mixins, viewsets
from adrf.mixins import Response, get_data
from asgiref.sync import sync_to_async
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken

from .models import CustomUser
from .serializers import (
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    UserSerializer,
)
from .tasks import send_password_reset_email


class RegisterViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle]

    async def acreate(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        await sync_to_async(serializer.is_valid)(raise_exception=True)
        user = await serializer.asave()

        token = await sync_to_async(RefreshToken.for_user)(user)
        user_data = await get_data(UserSerializer(user))

        return Response(
            {
                "user": user_data,
                "access": str(token.access_token),
                "refresh": str(token),
            },
            status=status.HTTP_201_CREATED,
        )


class UserMeViewSet(viewsets.GenericViewSet):
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)

    @action(detail=False, methods=["get", "patch"], url_path="me")
    async def me(self, request):
        if request.method == "PATCH":
            serializer = self.get_serializer(
                request.user, data=request.data, partial=True
            )
            await sync_to_async(serializer.is_valid)(raise_exception=True)
            await serializer.asave()
            user_data = await get_data(serializer)
            return Response(user_data)

        user_data = await get_data(self.get_serializer(request.user))
        return Response(user_data)

    @action(detail=False, methods=["post"], url_path="mark-notifications-seen")
    async def mark_notifications_seen(self, request):
        request.user.notifications_last_seen_at = timezone.now()
        await request.user.asave(update_fields=["notifications_last_seen_at"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class PasswordResetViewSet(viewsets.GenericViewSet):
    permission_classes = (AllowAny,)
    throttle_classes = (AnonRateThrottle,)

    def get_serializer_class(self):
        if self.action == "confirm":
            return PasswordResetConfirmSerializer
        return PasswordResetRequestSerializer

    async def acreate(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        await sync_to_async(serializer.is_valid)(raise_exception=True)

        user = await CustomUser.objects.filter(
            email__iexact=serializer.validated_data["email"]
        ).afirst()
        if user is not None:
            token = PasswordResetTokenGenerator().make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            await sync_to_async(send_password_reset_email.delay)(user.pk, uid, token)

        return Response(status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"])
    async def confirm(self, request):
        serializer = self.get_serializer(data=request.data)
        await sync_to_async(serializer.is_valid)(raise_exception=True)
        await serializer.asave()
        return Response(status=status.HTTP_200_OK)
