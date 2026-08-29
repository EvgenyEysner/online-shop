from django.contrib.auth.forms import UserChangeForm as BaseUserChangeForm
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm

from .models import CustomUser


class CustomUserChangeForm(BaseUserChangeForm):
    """
    Django's UserChangeForm verdrahtet 'Meta.model' hart auf
    django.contrib.auth.models.User und erwartet ein username-Feld.
    CustomUser nutzt email als USERNAME_FIELD.
    Das ReadOnlyPasswordHashField-Verhalten
    für password wird von der Basisklasse geerbt.
    """

    class Meta(BaseUserChangeForm.Meta):
        model = CustomUser
        field_classes = {}  # kein "username"-Feld -> kein UsernameField-Override nötig


class CustomUserCreationForm(BaseUserCreationForm):
    """
    Analog zu CustomUserChangeForm, für das Formular "Neuer Benutzer".
    """

    class Meta(BaseUserCreationForm.Meta):
        model = CustomUser
        fields = ("email", "first_name", "last_name")
        field_classes = {}
