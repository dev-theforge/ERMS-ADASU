from django.db import models
from django.utils.translation import gettext_lazy as _


class Complaint(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        UNDER_REVIEW = 'under_review', _('Under Review')
        RESOLVED = 'resolved', _('Resolved')
        REJECTED = 'rejected', _('Rejected')

    student = models.ForeignKey('accounts.StudentProfile', on_delete=models.CASCADE, related_name='complaints')
    result = models.ForeignKey('results.Result', on_delete=models.CASCADE, related_name='complaints')
    subject = models.CharField(max_length=300)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    reviewed_by = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_complaints')
    admin_response = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Complaint #{self.pk} — {self.student.matric_number} ({self.status})"


class ComplaintComment(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
