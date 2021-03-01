import logging

from django.shortcuts import render
from django.urls import reverse
from django.http import HttpResponseRedirect
from .auth import (identity_exists, protected, create_identity, setup_session,
                   has_valid_session, are_identities_equal)
from .api import get_add_link, exchange_auth_code
from slack.models import SlackIdentity

logger = logging.getLogger(__name__)


def pre_install(request):
    """Log in with a slack user.
    it shows a button to send the client ID and request scopes, tries to
    determine if the app was properly activated with slack services."""
    if has_valid_session(request):
        return HttpResponseRedirect(reverse('menu:order-list'))
    wording = 'Add to Slack'
    if identity_exists():
        wording = 'Sign in with Slack'
    return render(request, 'slack/login.html', {
        'link_text': wording,
        'add_link': get_add_link()
    })


# slack redirect view (part of slack workflow)
# look for 'code' field for grant and 'state' field for authenticity
# send slack the 'code' and receive 'authed_user.access_token' and
# create session
def post_install(request):
    code = request.GET.get('code')
    id_dict = exchange_auth_code(code)
    if identity_exists():
        if are_identities_equal(id_dict):
            setup_session(request)
        else:
            logger.info('another user tried to log in')
            return HttpResponseRedirect(reverse('slack:login'))
    else:
        create_identity(id_dict, request)
    return HttpResponseRedirect(reverse('menu:order-list'))


@protected
def logout(request):
    request.session.flush()
    return HttpResponseRedirect(reverse('slack:login'))


@protected
def uninstall(request):
    request.session.flush()
    identity = SlackIdentity.load()
    identity.delete()
    return HttpResponseRedirect(reverse('slack:login'))
