import logging
import time

from typing import List, Dict, Tuple, Optional, Iterable
from urllib.parse import urlencode
from django.conf import settings
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from .auth import get_access_token

logger = logging.getLogger(__name__)


def get_add_link() -> str:
    """Returns a url that starts the OAuth2 process"""
    URL = 'https://slack.com/oauth/v2/authorize'
    params = {
        'user_scope': ','.join(settings.SLACK_SCOPES),
        'client_id': settings.SLACK_CLIENT_ID
    }
    return f'{URL}?{urlencode(params)}'

def exchange_auth_code(code: str) -> Dict:
    """Returns the identity hash for the OAuth2 authorization code"""
    try:
        client = WebClient()
        response = client.oauth_v2_access(
            client_id=settings.SLACK_CLIENT_ID,
            client_secret=settings.SLACK_CLIENT_SECRET,
            code=code
        )
        return {
            'access_token': response.get('authed_user').get('access_token'),
            'user_id': response.get('authed_user').get('id'),
            'team_id': response.get('team').get('id')
        }
    except SlackApiError as e:
        logger.error(f'exchange_auth_code: {e.response["error"]}')
        raise ValueError(e.response['error'])

def get_users() -> Iterable:
    try:
        client = WebClient(token=get_access_token())
        response = client.users_list()
        members = response.get('members')
        filtered_members = filter(lambda u: u.get('name') != 'slackbot' and u.get('is_bot') == False, members)
        if settings.NORA_ONLY_LOCALS:
            filtered_members = filter(lambda u: u.get('tz') == settings.TIME_ZONE, filtered_members)
        return map(lambda u: (u.get('id'), u.get('real_name')), filtered_members)
    except SlackApiError as e:
        logger.error(f'get_users: {e.response["error"]}')
        return []

def __send_private_message(channel: str, text: str, ts: str=None) -> Tuple[str, str]:
    """Private function to send messages to users or channels. The message is
    updated if the timestamp is provided"""
    method = 'chat.postMessage'
    params = {
        'text': text,
        'channel': channel,
        'as_user': True
    }
    if ts is not None:
        method = 'chat.update'
        params.update({'ts': ts})
    client = WebClient(token=get_access_token())
    response = client.api_call(method, json=params)
    return (response.get('channel'), response.get('ts'))

def send_private_message(channel: str, text: str, ts: Optional[str]=None) -> Tuple:
    """Wrapper around the previous function that allow it to overcome rate
    limitations"""
    try:
        return __send_private_message(channel, text, ts)
    except SlackApiError as e:
        if e.response['error'] == 'ratelimited':
            logger.info(f'send_private_message was rate-limited, waiting')
            delay = int(e.response.headers['Retry-After'])
            time.sleep(delay)
            return __send_private_message(channel, text, ts)
        else:
            logger.error(f'send_private_message: {e.response["error"]}')
            return (None, None)

def delete_message(channel: str, ts: str) -> bool:
    try:
        client = WebClient(token=get_access_token())
        client.chat_delete(channel=channel, ts=ts)
        return True
    except SlackApiError as e:
        logger.error(f'delete_message: {e.response["error"]}')
        return False

def create_reminder(user_id: str, text: str) -> bool:
    try:
        client.reminders_add(text=text, user=user_id, time='in 1 second')
        return True
    except SlackApiError as e:
        logger.error(f'create_reminder: {e.response["error"]}')
        return False