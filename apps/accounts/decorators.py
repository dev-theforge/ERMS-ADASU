from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('accounts:login')
            if request.user.role not in roles:
                messages.error(request, "You do not have permission to access this page.")
                return redirect('dashboard')
            if request.user.status != 'active':
                messages.warning(request, "Your account is not active. Please contact the administrator.")
                return redirect('accounts:login')
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


def admin_required(view_func):
    return role_required('admin')(view_func)


def lecturer_required(view_func):
    return role_required('lecturer')(view_func)


def student_required(view_func):
    return role_required('student')(view_func)


def parent_required(view_func):
    return role_required('parent')(view_func)
