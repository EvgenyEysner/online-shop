from typing import Any

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string


@shared_task(
    bind=True,
    max_retries=5,
    default_retry_delay=60,
    autoretry_for=(Exception,),
)
def send_password_reset_email(self: Any, user_id: int, uid: str, token: str) -> None:
    """
    Passwort-Reset-Link, ausgelöst von PasswordResetViewSet.request().
    Nutzer darf mehrfach einen Reset anfragen und
    entsprechend mehrfach diese E-Mail erhalten.
    """
    from apps.accounts.models import CustomUser

    user = CustomUser.objects.get(pk=user_id)
    reset_url = f"{settings.FRONTEND_URL}/reset-password?uid={uid}&token={token}"

    EmailMessage(
        subject="Passwort zurücksetzen",
        body=render_to_string(
            "accounts/emails/password_reset.txt",
            {"user": user, "reset_url": reset_url},
        ),
        to=[user.email],
    ).send()
