"""Backend-only SMTP delivery for authentication and account messages."""

from __future__ import annotations

import smtplib
import ssl
from email.message import EmailMessage

from app.core.config import Settings


def _build_message(settings: Settings, recipient: str, subject: str, body_plain: str) -> EmailMessage:
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.smtp_from_email
    message["To"] = recipient
    message.set_content(body_plain)
    return message


def _send(settings: Settings, recipient: str, subject: str, body_plain: str) -> None:
    if not settings.smtp_host or not settings.smtp_from_email:
        raise RuntimeError("The SMTP relay is not configured.")
    message = _build_message(settings, recipient, subject, body_plain)
    smtp_class = smtplib.SMTP_SSL if settings.smtp_use_ssl else smtplib.SMTP
    with smtp_class(settings.smtp_host, settings.smtp_port, timeout=15) as smtp:
        if settings.smtp_starttls and not settings.smtp_use_ssl:
            smtp.starttls(context=ssl.create_default_context())
        if settings.smtp_username:
            smtp.login(settings.smtp_username, settings.smtp_password)
        smtp.send_message(message)


def send_login_code(settings: Settings, recipient: str, code: str) -> None:
    _send(
        settings,
        recipient,
        "Your Risklocker login confirmation code",
        "Use this one-time confirmation code to sign in to Risklocker:\n\n"
        f"{code}\n\n"
        f"This code expires in {settings.auth_code_expire_minutes} minutes. "
        "If you did not request it, you can ignore this email.",
    )


def send_invitation_email(settings: Settings, recipient: str, code: str) -> None:
    _send(
        settings,
        recipient,
        "You have been invited to Risklocker",
        "A Risklocker Admin has created an account for you.\n\n"
        "Use this one-time confirmation code to sign in and activate your account:\n\n"
        f"{code}\n\n"
        f"This code expires in {settings.auth_code_expire_minutes} minutes. "
        "If you did not expect this invitation, contact your Risklocker administrator.",
    )


def send_role_notification(settings: Settings, recipient: str, new_role: str) -> None:
    _send(
        settings,
        recipient,
        "Your Risklocker account role has changed",
        f"Your Risklocker account role has been updated to {new_role}.\n\n"
        "Your sign-in and data access may change on your next visit. "
        "Contact your Risklocker administrator with any questions.",
    )


def send_status_notification(settings: Settings, recipient: str, new_status: str) -> None:
    subject = "Your Risklocker account has been activated" if new_status == "active" else "Your Risklocker account has been deactivated"
    body = (
        "Your Risklocker account has been activated. You may now sign in."
        if new_status == "active"
        else "Your Risklocker account has been deactivated. You can no longer sign in. "
        "Contact your Risklocker administrator with any questions."
    )
    _send(settings, recipient, subject, body)


def send_test_email(settings: Settings, recipient: str) -> None:
    _send(
        settings,
        recipient,
        "Risklocker SMTP Test",
        "This is a test message from the Risklocker SMTP relay.\n\n"
        "If you received this email, the SMTP connection is working correctly.",
    )


def validate_smtp_connection(settings: Settings) -> tuple[bool, str]:
    if not settings.smtp_host or not settings.smtp_from_email:
        return False, "SMTP_HOST and SMTP_FROM_EMAIL are not configured."
    try:
        smtp_class = smtplib.SMTP_SSL if settings.smtp_use_ssl else smtplib.SMTP
        with smtp_class(settings.smtp_host, settings.smtp_port, timeout=15) as smtp:
            if settings.smtp_starttls and not settings.smtp_use_ssl:
                smtp.starttls(context=ssl.create_default_context())
            if settings.smtp_username:
                smtp.login(settings.smtp_username, settings.smtp_password)
    except smtplib.SMTPAuthenticationError:
        return False, "SMTP authentication failed. Check SMTP_USERNAME and SMTP_PASSWORD."
    except smtplib.SMTPConnectError:
        return False, f"Could not connect to SMTP host {settings.smtp_host}:{settings.smtp_port}."
    except OSError as exc:
        return False, f"SMTP connection failed: {exc}."
    except Exception as exc:
        return False, f"SMTP validation failed: {exc}."
    return True, "SMTP connection validated successfully."
