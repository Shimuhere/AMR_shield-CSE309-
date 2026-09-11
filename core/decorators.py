from functools import wraps

from django.shortcuts import redirect


def role_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            if request.user.role not in roles:
                return redirect('dashboard_redirect')
            return view(request, *args, **kwargs)
        return wrapper
    return decorator
