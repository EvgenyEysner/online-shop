from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import CustomUserChangeForm, CustomUserCreationForm
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """
    Erbt bewusst von django.contrib.auth.admin.UserAdmin (nicht
    admin.ModelAdmin), um die eingebaute Passwort-Reset-URL/-View
    (<id>/password/, AdminPasswordChangeForm) sowie ReadOnlyPasswordHashField
    zu erben.
    """

    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    model = CustomUser

    # UserAdmin-Defaults referenzieren "username" - existiert hier nicht,
    # deshalb vollständig überschrieben:
    ordering = ("email",)
    list_display = (
        "customer_number",
        "email",
        "first_name",
        "last_name",
        "is_active",
        "is_staff",
    )
    search_fields = ("customer_number", "email", "first_name", "last_name")
    readonly_fields = ("customer_number", "created_at", "updated_at")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Persönliche Daten",
            {"fields": ("first_name", "last_name", "customer_number")},
        ),
        ("Adresse", {"fields": ("street", "street_no", "zip_code", "city", "country")}),
        (
            "Berechtigungen",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        ("Wichtige Daten", {"fields": ("last_login", "created_at", "updated_at")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "password1",
                    "password2",
                ),
            },
        ),
    )

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if request.user.is_superuser:
            return fieldsets
        # Nicht-Superuser dürfen Berechtigungsfelder weder sehen noch setzen.
        # Wirkt serverseitig: ModelAdmin.get_form() leitet die tatsächlichen
        # Formularfelder aus get_fieldsets() ab (flatten_fieldsets), nicht
        # nur die UI-Darstellung.
        restricted = {"is_superuser", "user_permissions", "groups"}
        return tuple(
            (
                name,
                {
                    **opts,
                    "fields": tuple(f for f in opts["fields"] if f not in restricted),
                },
            )
            for name, opts in fieldsets
        )
