from functools import wraps
from flask import abort, redirect, url_for, request, flash
from flask_login import current_user


def role_required(role):
    """
    Restrict access to users with specific role.
    Usage:
        @role_required('admin')
        @role_required('patient')
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please login to access this page.', 'info')
                return redirect(url_for('auth.login', next=request.url))

            if current_user.role != role:
                abort(403)

            return f(*args, **kwargs)
        return wrapped
    return decorator
