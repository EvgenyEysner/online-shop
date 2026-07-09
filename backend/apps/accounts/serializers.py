from adrf import serializers
from models import CustomUser


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
            "is_active",
            "is_staff",
            "date_joined",
            "password",
            "employee",
        ]
        read_only_fields = ["is_active", "is_staff", "is_superuser", "date_joined"]
