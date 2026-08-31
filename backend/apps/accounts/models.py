from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models

from apps.utils.helpers import Address
from .managers import UserManager


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    Custom User Model.
    """

    customer_number = models.CharField(
        "Kundennummer",
        max_length=16,
        unique=True,
        blank=True,
        null=True,
    )
    email = models.EmailField("E-Mail-Adresse", unique=True)
    first_name = models.CharField("Vorname", max_length=150)
    last_name = models.CharField("Nachname", max_length=150)

    street = models.CharField("Straße", max_length=255)
    street_no = models.CharField("Hausnummer", max_length=255, blank=True)
    zip_code = models.CharField("PLZ", max_length=5)
    city = models.CharField("Ort", max_length=255)
    country = models.CharField("Land", max_length=255, default="Deutschland")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notifications_last_seen_at = models.DateTimeField(
        "Benachrichtigungen zuletzt gesehen am",
        null=True,
        blank=True,
        help_text="Gesetzt von UserMeViewSet.mark_notifications_seen() - "
        "Ereignisse mit occurred_at danach gelten als ungelesen. None bedeutet: alle Ereignisse sind ungelesen.",
    )

    is_staff = models.BooleanField(
        "staff status",
        default=False,
        help_text="Designates whether the user can log into this admin site.",
    )
    is_active = models.BooleanField(
        "active",
        default=True,
        help_text=(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts."
        ),
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = UserManager()

    class Meta:
        ordering = ["email"]
        verbose_name = "Benutzer"
        verbose_name_plural = "Benutzer"

    def __str__(self) -> str:
        return self.email

    def save(self, *args, **kwargs):
        self.email = self.__class__.objects.normalize_email(self.email)
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def address(self) -> Address:
        return Address(
            first_name=self.first_name,
            last_name=self.last_name,
            street=self.street,
            street_no=self.street_no,
            zip_code=self.zip_code,
            city=self.city,
            country=self.country,
        )

    def as_checkout_shipping(self) -> dict:
        """
        Shipping payload for Stripe checkout (guest/logged-in).
        """
        return self.address().as_checkout_shipping()
