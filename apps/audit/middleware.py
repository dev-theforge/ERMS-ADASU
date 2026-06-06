from .models import AuditLog


class AuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.user.is_authenticated and request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            ip = request.META.get('REMOTE_ADDR')
            ua = request.META.get('HTTP_USER_AGENT', '')[:500]
            AuditLog.log(
                user=request.user,
                action=f"{request.method} {request.path}",
                ip=ip,
                ua=ua
            )

        if request.user.is_authenticated:
            request.user.last_login_ip = request.META.get('REMOTE_ADDR')
            request.user.save(update_fields=['last_login_ip'])

        return response