import smtplib
from email.message import EmailMessage
from app.core.config import settings


def password_reset_email_configured() -> bool:
    return bool(
        settings.SMTP_HOST
        and settings.SMTP_USER
        and settings.SMTP_PASSWORD
        and settings.SMTP_FROM_EMAIL
        and settings.frontend_url
    )


def _send_email(message: EmailMessage) -> None:
    if settings.SMTP_USE_SSL:
        with smtplib.SMTP_SSL(
            settings.SMTP_HOST,
            settings.SMTP_PORT,
            timeout=settings.SMTP_TIMEOUT_SECONDS
        ) as smtp:
            smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            smtp.send_message(message)
        return

    with smtplib.SMTP(
        settings.SMTP_HOST,
        settings.SMTP_PORT,
        timeout=settings.SMTP_TIMEOUT_SECONDS
    ) as smtp:
        smtp.ehlo()
        if settings.SMTP_USE_STARTTLS:
            smtp.starttls()
            smtp.ehlo()
        smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        smtp.send_message(message)


def send_password_reset_email(recipient: str, reset_url: str) -> None:
    message = EmailMessage()
    message["Subject"] = "Reset your MediAssist AI password"
    message["From"] = settings.SMTP_FROM_EMAIL
    message["To"] = recipient
    message.set_content(
        "We received a request to reset your MediAssist AI password.\n\n"
        f"Use this one-time link within {settings.PASSWORD_RESET_TOKEN_MINUTES} minutes:\n"
        f"{reset_url}\n\n"
        "If you did not request this reset, you can ignore this email. "
        "Your password will not change unless the link is used."
    )

    _send_email(message)


def feedback_email_configured() -> bool:
    return bool(
        settings.SMTP_HOST
        and settings.SMTP_USER
        and settings.SMTP_PASSWORD
        and settings.SMTP_FROM_EMAIL
        and settings.FEEDBACK_RECIPIENT_EMAIL
    )


def send_feedback_email(
    sender_name: str,
    sender_email: str,
    category: str,
    rating: int,
    feedback: str
) -> None:
    message = EmailMessage()
    message["Subject"] = f"MediAssist AI patient feedback: {category}"
    message["From"] = settings.SMTP_FROM_EMAIL
    message["To"] = settings.FEEDBACK_RECIPIENT_EMAIL
    message["Reply-To"] = sender_email
    message.set_content(
        "A patient submitted feedback about the MediAssist AI platform.\n\n"
        f"Patient name: {sender_name}\n"
        f"Patient email: {sender_email}\n"
        f"Category: {category}\n"
        f"Rating: {rating}/5\n\n"
        "Feedback:\n"
        f"{feedback}\n"
    )
    _send_email(message)
