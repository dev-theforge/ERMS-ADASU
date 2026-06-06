"""
Async notification tasks using Celery.
Falls back gracefully if Celery/Redis not available.
"""
import logging
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def send_email_notification(recipient_email, subject, message):
    """Send email notification via SendGrid/Django email backend."""
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            fail_silently=False,
        )
        logger.info(f"Email sent to {recipient_email}: {subject}")
        return True
    except Exception as e:
        logger.error(f"Email failed to {recipient_email}: {e}")
        return False


def send_sms_notification(phone_number, message):
    """Send SMS via Twilio."""
    sid = getattr(settings, 'TWILIO_ACCOUNT_SID', '')
    token = getattr(settings, 'TWILIO_AUTH_TOKEN', '')
    from_number = getattr(settings, 'TWILIO_PHONE_NUMBER', '')

    if not all([sid, token, from_number]):
        logger.debug("Twilio not configured — skipping SMS")
        return False

    try:
        from twilio.rest import Client
        client = Client(sid, token)
        client.messages.create(body=message, from_=from_number, to=phone_number)
        logger.info(f"SMS sent to {phone_number}")
        return True
    except Exception as e:
        logger.error(f"SMS failed to {phone_number}: {e}")
        return False


def notify_user(user, subject, message):
    """Send both email and SMS notification to a user."""
    if user.email:
        send_email_notification(user.email, subject, message)
    if user.phone_number:
        send_sms_notification(user.phone_number, message)
