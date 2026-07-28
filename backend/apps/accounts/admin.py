from django.contrib import admin

from apps.core.services.allocation import GlobalIdentifier
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ("customer_number", "email", "first_name", "last_name", "is_active")
    search_fields = ("customer_number", "email", "first_name", "last_name")
    readonly_fields = ("customer_number", "created_at", "updated_at")


@admin.register(GlobalIdentifier)
class GlobalIdentifierAdmin(admin.ModelAdmin):
    list_display = ("key", "value")
    search_fields = ("key",)
    readonly_fields = ("key", "value")
