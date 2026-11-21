from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from .models import User


def role_required(*allowed_roles):
    """
    Decorator for views that checks whether a user has a specific role.
    Raises PermissionDenied (403) if unauthorized.
    Superusers always have access to admin-level views.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            # Superuser gets admin access automatically
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
                
            if request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)
                
            raise PermissionDenied("You do not have permission to access this portal page.")
        return _wrapped_view
    return decorator


def participant_required(view_func):
    return role_required(User.Role.PARTICIPANT)(view_func)


def coordinator_required(view_func):
    return role_required(User.Role.COORDINATOR)(view_func)


def professional_required(view_func):
    return role_required(User.Role.PROFESSIONAL)(view_func)


def hr_required(view_func):
    return role_required(User.Role.HR, User.Role.ADMIN)(view_func)


def admin_required(view_func):
    return role_required(User.Role.ADMIN)(view_func)
