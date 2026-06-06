from django.db import models


class AuditLog(models.Model):
    user = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    action = models.CharField(max_length=200)
    model_name = models.CharField(max_length=100, blank=True)
    object_id = models.CharField(max_length=50, blank=True)
    object_repr = models.CharField(max_length=300, blank=True)
    changes = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {self.user} — {self.action}"

    @classmethod
    def log(cls, user, action, model_name='', object_id='', object_repr='', changes=None, ip=None, ua=''):
        return cls.objects.create(
            user=user, action=action, model_name=model_name,
            object_id=str(object_id), object_repr=object_repr,
            changes=changes or {}, ip_address=ip, user_agent=ua
        )
