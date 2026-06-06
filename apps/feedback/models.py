from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator


class Feedback(models.Model):
    class Category(models.TextChoices):
        GENERAL = 'general', _('General')
        RESULTS = 'results', _('Result Management')
        COMPLAINTS = 'complaints', _('Complaint System')
        NOTIFICATIONS = 'notifications', _('Notifications')
        PORTAL = 'portal', _('Portal Usability')

    author = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='feedbacks')
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.GENERAL)
    subject = models.CharField(max_length=300)
    message = models.TextField()
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Feedback from {self.author.username}: {self.subject}"
