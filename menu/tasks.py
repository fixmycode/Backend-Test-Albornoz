from django.conf import settings
from django.utils.timezone import localtime, now
from celery import shared_task
from celery.utils.log import get_task_logger

from menu.models import Menu, Order
from slack.api import (get_users, create_reminder,
                       send_private_message, delete_message)

logger = get_task_logger(__name__)

# Menu triggered tasks

@shared_task
def create_orders(menu_id):
    menu = Menu.objects.get(pk=menu_id)
    users = get_users()
    for user_id, user_name in users:
        Order.objects.get_or_create(
            employee_slack_id=user_id,
            employee_real_name=user_name,
            menu=menu)
    if settings.NORA_NOTIFY_HOUR == -1:
        send_reminders(menu_id=menu_id)


@shared_task
def notify_menu_change(menu_id):
    """If a menu is updated and has already sent reminders to the users,
    this task will do two things:
    - it will update the message for all the users that haven't made a
      selection yet.
    - if the user already has selected an option it will send a message
      to the user saying that the menu has changed. It will also tell the
      users if their option was removed."""
    orders = Order.objects.filter(
        menu_id=menu_id, 
        fulfilled__isnull=True, 
        sent__isnull=False)
    for order in orders:
        update_order(order.pk)
        if order.selected is not None:
            text = ('Sorry to bother you again but today\'s menu has changed '
                    'and you may want to check it out 👀 maybe you like it better.')
            if order.selected not in order.menu.options:
                text += ' *Your previous choice is no longer available or it changed.*'
            send_private_message(order.employee_slack_id, text)


@shared_task
def notify_menu_deleted(menu_id):
    """If a menu is deleted and has already sent reminders to users,
    this task will do two things:
    - it will delete the message for all users.
    - it will send a new message to users who had made a selection, telling
      them to wait for a new menu.
    Q: why not just editing the order message?
    A: We want them to get notified that they're not receiving their lunch."""
    menu = Menu.objects.get(pk=menu_id)
    orders = Order.objects.filter(
        menu=menu, fulfilled__isnull=True, sent__isnull=False)
    for order in orders:
        delete_message(order.employee_channel, order.ts)
        if order.selected:
            text = ('There was a mistake with the previous menu, but I\'ll '
                    'contact you shorty with a new one. Sorry!! 😅')
            send_private_message(order.employee_slack_id, text)
        order.delete()
    menu.delete()


# Order triggered tasks

@shared_task
def update_order(order_id):
    """This will update the message sent to an user. It's called when the user
    makes a selection or when the menu is changed.
    """
    order = Order.objects.get(pk=order_id)
    channel, ts = send_private_message(
        order.employee_channel, 
        order.reminder_text, 
        order.ts)
    order.employee_channel = channel
    order.ts = ts
    order.save()

# Periodic tasks

@shared_task
def send_reminders(menu_id=None):
    """Sends the messages to the users related to this menu.
    This task is scheduled to occur at the day of the menu, at the hour set by
    NOTIFY_HOUR in the settings.
    If the SLACK_USE_REMINDERS option is set, it will use reminders instead of
    sending direct messages, but reminders can't be updated, so much of the
    usability of the app will be lost."""
    if menu_id:
        menus = Menu.objects.filter(pk=menu_id)
    else:
        local_now = localtime(now())
        menus = Menu.objects.filter(date=local_now.date())
    for menu in menus:
        orders = menu.orders.filter(sent__isnull=True)
        logger.info(f'Sending {len(orders)} reminders for menu {menu.id}...')
        for order in orders:
            text = order.reminder_text
            if settings.SLACK_USE_REMINDERS:
                create_reminder(order.employee_slack_id, text)
            else:
                channel, ts = send_private_message(
                    order.employee_slack_id, text)
                order.employee_channel = channel
                order.ts = ts
            order.sent = now()
            order.save()
        menu.sent = now()
        menu.save()
