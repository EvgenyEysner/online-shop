from django.contrib import admin

from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ("customer_number", "email", "first_name", "last_name", "is_active")
    search_fields = ("customer_number", "email", "first_name", "last_name")
    readonly_fields = ("customer_number", "created_at", "updated_at")
