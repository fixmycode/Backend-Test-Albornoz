import pytest

from django.utils.timezone import now

from menu.tasks import (create_orders, notify_menu_change, notify_menu_deleted,
    update_order, send_reminders)
from menu.models import Menu, Order
from .utils import setup_models


pytestmark = pytest.mark.django_db


def test_create_orders(mocker, settings):
    settings.NORA_NOTIFY_HOUR = -1
    menu, order = setup_models(days=1)
    mocker.patch('menu.tasks.get_users', return_value=[('a', 'b'), ('c', 'd')])
    send_reminders = mocker.patch('menu.tasks.send_reminders')
    create_orders(menu.id)
    send_reminders.assert_called_with(menu_id=menu.id)
    assert menu.orders.count() == 3

    # multiple calls should not create more orders
    create_orders(menu.id)
    assert menu.orders.count() == 3

def test_notify_menu_change(mocker):
    menu, order = setup_models(days=1)
    update_order = mocker.patch('menu.tasks.update_order')
    send_private_message = mocker.patch('menu.tasks.send_private_message')
    order.sent = now()
    order.save()
    

    # order is not selected. it wont send a message
    notify_menu_change(menu.id)
    update_order.assert_called_with(order.pk)
    send_private_message.assert_not_called()

    order.selected = menu.options[0]
    order.save()

    # order is selected. it will send a message
    update_order.reset_mock()
    send_private_message.reset_mock()
    
    notify_menu_change(menu.id)
    update_order.assert_called_with(order.pk)
    send_private_message.assert_called()

def test_notify_menu_deleted(mocker):
    menu, order = setup_models(days=1)
    delete_message = mocker.patch('menu.tasks.delete_message')
    order.sent = now()
    order.employee_channel = 'a'
    order.ts = 'b'
    order.save()
    notify_menu_deleted(menu.id)
    delete_message.assert_called_with('a', 'b')

def test_update_order(mocker):
    _, order = setup_models()
    send_private_message = mocker.patch(
        'menu.tasks.send_private_message', return_value=('a','b'))
    assert order.employee_channel == None
    assert order.ts == None
    update_order(order.id)
    order.refresh_from_db()
    assert order.employee_channel == 'a'
    assert order.ts == 'b'

def test_send_reminders_pm(mocker):
    menu, order = setup_models()
    create_reminder = mocker.patch('menu.tasks.create_reminder')
    send_private_message = mocker.patch('menu.tasks.send_private_message', return_value=('a', 'b'))
    assert order.sent == None
    send_reminders(menu_id=menu.id)
    order.refresh_from_db()
    assert order.sent != None
    assert order.employee_channel == 'a'
    assert order.ts == 'b'
    create_reminder.assert_not_called()
    send_private_message.assert_called_with(order.employee_slack_id, order.reminder_text)

def test_send_reminders(mocker, settings):
    menu, order = setup_models()
    settings.SLACK_USE_REMINDERS = True
    create_reminder = mocker.patch('menu.tasks.create_reminder')
    send_private_message = mocker.patch('menu.tasks.send_private_message', return_value=('a', 'b'))
    assert order.sent == None
    send_reminders(menu_id=menu.id)
    order.refresh_from_db()
    assert order.sent != None
    create_reminder.assert_called_with(order.employee_slack_id, order.reminder_text)
    send_private_message.assert_not_called()