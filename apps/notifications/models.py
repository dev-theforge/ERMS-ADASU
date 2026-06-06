from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.validators import validate_email
from django.core.exceptions import ValidationError


class Notification(models.Model):

    class NType(models.TextChoices):
        ACCOUNT_APPROVAL = 'account_approval', _('Account Approved')
        ACCOUNT_REJECTION = 'account_rejection', _('Account Rejected')
        RESULT_PUBLISHED = 'result_published', _('Result Published')
        COMPLAINT_UPDATE = 'complaint_update', _('Complaint Update')
        GPA_WARNING = 'gpa_warning', _('GPA Warning')
        RESULT_SUBMITTED = 'result_submitted', _('Result Submitted')
        PASSWORD_CHANGED = 'password_changed', _('Password Changed')
        GENERAL = 'general', _('General')

    recipient = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.CASCADE,
        related_name='notifications'
    )

    notification_type = models.CharField(
        max_length=30,
        choices=NType.choices,
        default=NType.GENERAL
    )

    title = models.CharField(max_length=300)
    message = models.TextField()

    is_read = models.BooleanField(default=False)

    action_url = models.CharField(
        max_length=500,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"→ {self.recipient.username}: {self.title}"

    @classmethod
    def notify(cls, recipient, ntype, title, message, url=''):
       

        notification = cls.objects.create(
            recipient=recipient,
            notification_type=ntype,
            title=title,
            message=message,
            action_url=url
        )



        

        # Send Email
        if recipient.email:
            try:
                validate_email(recipient.email)

                email = EmailMultiAlternatives(
                    subject=title,
                    body=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[recipient.email]
                )

                html_content = f"""
                <html>
                    <body>
                        <h2>{title}</h2>
                        <p>{message}</p>
                        <hr>
                        <p>
                            Rev. Fr. Moses Orshio Adasu University<br>
                            Examination Results Management System (ERMS)
                        </p>
                    </body>
                </html>
                """

                email.attach_alternative(html_content, "text/html")
                email.send(fail_silently=False)

            except ValidationError:
                print(
                    f"Invalid email address for "
                    f"{recipient.username}: {recipient.email}"
                )

            except Exception as e:
                print(f"Email sending failed: {e}")

        return notification
  

    ...