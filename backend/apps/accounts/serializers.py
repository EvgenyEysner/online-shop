from adrf import serializers

from .models import CustomUser


class UserSerializer(serializers.ModelSerializer):
    # perms = serializers.SerializerMethodField(read_only=True)
    #
    # def get_perms(self, obj):
    #     return hasattr(obj, "employee") and obj.employee.permission_group

    class Meta:
        model = CustomUser
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "is_active",
            "is_staff",
            "password",
        ]
        read_only_fields = ["is_active", "is_staff", "is_superuser"]
