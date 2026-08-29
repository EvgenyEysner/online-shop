from django.contrib import admin

from .models import GlobalIdentifier


@admin.register(GlobalIdentifier)
class GlobalIdentifierAdmin(admin.ModelAdmin):
    list_display = ("key", "value")
    search_fields = ("key",)
    readonly_fields = ("key", "value")
