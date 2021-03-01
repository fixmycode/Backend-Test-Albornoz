from django.utils.timezone import localtime, now
from datetime import timedelta
from uuid import uuid4

from menu.models import Menu, Order

def setup_models(days=1, orders=1, no_menu=False):
    factor = days/abs(days) if days != 0 else 1
    date = localtime(now()).date() + factor*timedelta(days=abs(days))
    options = ['a', 'b', 'c']
    menu = Menu.objects.create(date=date, options=options) if not no_menu else None
    order_list = []
    for i in range(max(orders, 1)):
        order_list.append(
            Order.objects.create(
                employee_slack_id=str(uuid4())[:8], 
                employee_real_name='Unique User', 
                menu=menu
            )
        )
    order = order_list if orders > 1 else order_list[0]
    return menu, order