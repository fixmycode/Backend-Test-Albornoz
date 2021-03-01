import pytest

from django.core.validators import URLValidator
from slack.api import (get_add_link, exchange_auth_code, WebClient, get_users,
    send_private_message, delete_message, create_reminder)

pytestmark = pytest.mark.django_db

def test_get_add_link():
    url = get_add_link()
    validator = URLValidator()
    validator(url)

def test_exchange_auth_code(mocker, settings):
    method = mocker.patch.object(WebClient, 'oauth_v2_access')
    exchange_auth_code('a')
    method.assert_called_with(
        client_id=settings.SLACK_CLIENT_ID,
        client_secret=settings.SLACK_CLIENT_SECRET,
        code='a')

def test_get_users(mocker, settings):
    test_clients = [
        {'name': 'test1', 'is_bot': False, 'tz': settings.TIME_ZONE, 
        'id': 1, 'real_name': 'Test 1'},
        {'name': 'test2', 'is_bot': True, 'tz': settings.TIME_ZONE,
        'id': 2, 'real_name': 'Test 2'},
        {'name': 'test3', 'is_bot': False, 'tz': 'Oceania',
        'id': 3, 'real_name': 'Test 3'}
    ]
    mocker.patch('slack.api.get_access_token')
    method = mocker.patch.object(WebClient, 'users_list', 
        return_value={'members': test_clients})
    # only locals
    settings.NORA_ONLY_LOCALS = True
    res = list(get_users())
    assert (1, 'Test 1') in res
    assert (2, 'Test 2') not in res
    assert (3, 'Test 3') not in res

    # not only locals
    settings.NORA_ONLY_LOCALS = False
    res = list(get_users())
    assert (1, 'Test 1') in res
    assert (2, 'Test 2') not in res
    assert (3, 'Test 3') in res

def test_send_private_message(mocker):
    method = mocker.patch.object(WebClient, 'api_call', 
        return_value={'channel': 'a', 'ts': 'b'})
    res = send_private_message('a', 'c', 'b')
    method.assert_called()
    assert res == ('a', 'b')

def test_delete_message(mocker):
    method = mocker.patch.object(WebClient, 'chat_delete')
    delete_message('a', 'b')
    method.assert_called_with(channel='a', ts='b')

def create_reminder(mocker):
    method = mocker.patch.object(WebClient, 'reminders_add')
    create_reminder('a', 'b')
    method.assert_called_with(text='b', user='a')