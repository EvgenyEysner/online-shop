from adrf import viewsets
from adrf.mixins import Response
from django.http import Http404
from models import CustomUser
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from serializers import UserSerializer


class UserMeViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)

    @action(detail=False, methods=["get", "patch"], url_path="me")
    async def me(self, request):
        if request.method == "PATCH":
            serializer = self.get_serializer(
                request.user, data=request.data, partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        return Response(self.get_serializer(request.user).data)
