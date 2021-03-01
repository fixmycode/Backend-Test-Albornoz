import logging
import functools

from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect, HttpRequest

from .models import SlackIdentity

logger = logging.getLogger(__name__)

SESSION_KEY = 'file_key'


def create_identity(id_dict: dict, request: HttpRequest):
    SlackIdentity.objects.create(**id_dict)
    setup_session(request)


def are_identities_equal(id_dict: dict) -> bool:
    try:
        SlackIdentity.objects.get(**id_dict)
        return True
    except SlackIdentity.DoesNotExist as _:
        pass
    return False


def setup_session(request: HttpRequest):
    key = SlackIdentity.get_identity_hash()
    request.session[SESSION_KEY] = key


def identity_exists() -> bool:
    """Ensures the identity record exists and it's only one"""
    return SlackIdentity.objects.count() == 1


def check_user_identity(request) -> bool:
    try:
        if identity_exists():
            id_key = request.session.get(SESSION_KEY)
            id_hash = SlackIdentity.get_identity_hash()
            return id_key == id_hash
    except SlackIdentity.DoesNotExist as _:
        pass
    return False


def has_valid_session(request: HttpRequest) -> bool:
    """validates that the user session is legitimate"""
    if not request.session:
        return False
    key = request.session.get(SESSION_KEY)
    if not key:
        return False
    if not identity_exists():
        return False
    if key != SlackIdentity.get_identity_hash():
        return False
    return True


def get_access_token():
    identity = SlackIdentity.load()
    return identity.access_token


def delete_session(request):
    try:
        del request.session[SESSION_KEY]
        request.session.flush()
    except KeyError as _:
        logger.info('no session found')


def protected(function=None, **kw0):
    """Decorator that ensures the user identity is the same as the user that
    installed the app the first time"""
    redirect_to = kw0.get('redirect_to', None)

    def decorator(view_func, *ar1, **kw1):
        @functools.wraps(view_func)
        def wrapper_protect(request, *ar2, **kw2):
            if check_user_identity(request):
                return view_func(request, *ar2, **kw2)
            if redirect_to:
                return HttpResponseRedirect(redirect_to)
            raise PermissionDenied()
        return wrapper_protect
    if function:
        return decorator(function)
    return decorator
