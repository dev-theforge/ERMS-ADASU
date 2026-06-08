from django.db import models
from django.utils.translation import gettext_lazy as _
import logging

logger = logging.getLogger(__name__)


class Notification(models.Model):
    class NType(models.TextChoices):
        ACCOUNT_APPROVAL  = 'account_approval',  _('Account Approved')
        ACCOUNT_REJECTION = 'account_rejection',  _('Account Rejected')
        RESULT_PUBLISHED  = 'result_published',   _('Result Published')
        COMPLAINT_UPDATE  = 'complaint_update',   _('Complaint Update')
        GPA_WARNING       = 'gpa_warning',        _('GPA Warning')
        RESULT_SUBMITTED  = 'result_submitted',   _('Result Submitted')
        PASSWORD_CHANGED  = 'password_changed',   _('Password Changed')
        GENERAL           = 'general',            _('General')

    recipient         = models.ForeignKey(
        'accounts.CustomUser', on_delete=models.CASCADE, related_name='notifications'
    )
    notification_type = models.CharField(
        max_length=30, choices=NType.choices, default=NType.GENERAL
    )
    title      = models.CharField(max_length=300)
    message    = models.TextField()
    is_read    = models.BooleanField(default=False)
    action_url = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at    = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'→ {self.recipient.username}: {self.title}'

    # ------------------------------------------------------------------
    # Central dispatcher — every call saves in-app AND fires email + SMS
    # ------------------------------------------------------------------
    @classmethod
    def notify(cls, recipient, ntype, title, message, url='',
               send_email=True, send_sms=True):
        """
        Create an in-app notification and automatically send email + SMS.

        Parameters
        ----------
        recipient  : CustomUser instance
        ntype      : Notification.NType string, e.g. 'result_published'
        title      : Short subject line shown in bell icon and email subject
        message    : Full message body
        url        : Optional relative URL for the action button
        send_email : Pass False to suppress email for this specific call
        send_sms   : Pass False to suppress SMS for this specific call
        """
        # 1. Always save the in-app notification first
        obj = cls.objects.create(
            recipient=recipient,
            notification_type=ntype,
            title=title,
            message=message,
            action_url=url,
        )

        # 2. Fire email and SMS — wrapped in try/except so a delivery
        #    failure never crashes the main Django request
        try:
            from apps.notifications.tasks import notify_user
            notify_user(
                user=recipient,
                subject=f'ERMS — {title}',
                message=_build_email_body(recipient, title, message),
                send_email=send_email,
                send_sms=send_sms,
            )
        except Exception:
            logger.exception(
                'Notification delivery failed for pk=%s recipient=%s',
                obj.pk, recipient.username
            )

        return obj


def _build_email_body(recipient, title, message):
    """Wrap the message in a clean plain-text email body."""
    name = recipient.get_full_name() or recipient.username
    return (
        f"Dear {name},\n\n"
        f"{message}\n\n"
        f"---\n"
        f"This is an automated message from the ERMS portal.\n"
        f"Rev. Fr. Moses Orshio Adasu University, Makurdi, Benue State.\n"
        f"Please do not reply to this email.\n"
        f"For support contact: erms-support@adasu.edu.ng"
    )
