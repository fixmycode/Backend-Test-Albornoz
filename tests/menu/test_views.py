import pytest

from django.urls import reverse
from django.utils.timezone import localtime, now
from datetime import timedelta

from menu.models import Menu
from .utils import setup_models


pytestmark = pytest.mark.django_db


@pytest.fixture
def auth_client(mocker, client):
    mocker.patch('slack.views.exchange_auth_code',
                 return_value={'user_id': 'a',
                               'team_id': 'a',
                               'access_token': 'a'})
    client.get(reverse('slack:auth')+'?code=dfg')
    return client


def test_protected_views(client, mocker):
    menu, order = setup_models()

    def assert_view_for_code(names, status_code, **kwargs):
        for name in names:
            url = reverse(f'menu:{name}', kwargs=kwargs)
            res = client.get(url)
            assert res.status_code == status_code

    def assert_for_code(status_code):
        assert_view_for_code(['menu-create', 'menu-list'], status_code)
        assert_view_for_code(
            ['menu-update', 'menu-delete'], status_code, pk=menu.id)

    # without session, root should redirect to login
    assert_view_for_code(['order-list'], 302)

    # other views will return 403 forbidden
    assert_for_code(403)

    # logging in the user
    mocker.patch('slack.views.exchange_auth_code',
                 return_value={'user_id': 'a',
                               'team_id': 'a',
                               'access_token': 'a'})
    client.get(reverse('slack:auth')+'?code=dfg')

    # with the session, all views should return 200 ok
    assert_for_code(200)


class TestListOrder:
    """We are not trying to test integration, we test the views processes"""

    def test_dates(self, auth_client):
        days_in_the_future = 3
        menu, order = setup_models(days=days_in_the_future)
        order.selected = 'a'
        order.sent = order.created
        order.save()
        res = auth_client.get(reverse('menu:order-list'))
        dates = res.context.get('dates')
        assert len(dates) == 2
        today, future = dates
        assert today == localtime(now()).date()
        assert future == (
            localtime(now()) + timedelta(days=days_in_the_future)).date()

    def test_select_date(self, auth_client):
        date_in_the_future = (localtime(now()) + timedelta(days=5)).date()
        date_string = date_in_the_future.strftime('%Y%m%d')
        res = auth_client.get(reverse('menu:order-list')+f'?d={date_string}')
        selected_date = res.context.get('selected_date')
        assert selected_date == date_in_the_future

    def test_order_states(self, auth_client):
        menu, order = setup_models(days=1)
        date_in_the_future = (localtime(now()) + timedelta(days=1)).date()
        date_string = date_in_the_future.strftime('%Y%m%d')

        def check_state(client):
            res = client.get(reverse('menu:order-list')+f'?d={date_string}')
            pending_orders = res.context.get('pending_orders')
            active_orders = res.context.get('active_orders')
            ready_orders = res.context.get('ready_orders')
            return pending_orders, len(active_orders), len(ready_orders)

        # 1 order is created
        states = check_state(auth_client)
        assert states == (0, 0, 0)

        order.sent = order.created
        order.save()

        # 2 order is sent, it becomes pending
        states = check_state(auth_client)
        assert states == (1, 0, 0)

        order.selected = 'a'
        order.save()

        # 3 order is selected, it becomes active
        states = check_state(auth_client)
        assert states == (0, 1, 0)

        order.fulfilled = order.created
        order.save()

        # 3 order is fulfilled, it becomes ready
        states = check_state(auth_client)
        assert states == (0, 0, 1)


class TestCreateMenu:
    def test_create(self, auth_client, mocker):
        present = localtime(now())
        date_in_the_future = (present + timedelta(days=5)).date()

        mocker.patch('menu.views.create_orders')

        res = auth_client.post(
            reverse('menu:menu-create'),
            {'date': date_in_the_future, 'options': '["a", "b", "c"]'})
        assert res.status_code == 302

        res = auth_client.post(
            reverse('menu:menu-create'),
            {'options': '["a", "b", "c"]'})
        assert res.status_code == 400


class TestUpdateMenu:
    def test_update(self, auth_client, mocker):
        menu, order = setup_models(days=1)

        present = localtime(now())
        date_in_the_future = (present + timedelta(days=5)).date()
        date_in_the_past = (present - timedelta(days=3)).date()

        mocker.patch('menu.views.notify_menu_change')

        res = auth_client.post(
            reverse('menu:menu-update', kwargs={'pk': menu.pk}),
            {'date': date_in_the_future, 'options': '["a", "b", "c"]'})
        assert res.status_code == 302

        res = auth_client.post(
            reverse('menu:menu-update', kwargs={'pk': menu.pk}),
            {'date': date_in_the_past, 'options': '["a", "b", "c"]'})
        assert res.status_code == 400


class TestListMenu:
    def test_list(self, auth_client):
        # test no menus
        res = auth_client.get(reverse('menu:menu-list'))
        assert len(res.context.get('object_list')) == 0

        # test 1 menu
        menu, _ = setup_models(days=1)
        res = auth_client.get(reverse('menu:menu-list'))
        assert len(res.context.get('object_list')) == 1

        # test 10 menus
        models = [setup_models(days=1) for i in range(9)]
        res = auth_client.get(reverse('menu:menu-list'))
        assert len(res.context.get('object_list')) == 10


class TestDeleteMenu:
    def test_delete_confirm(self, auth_client):
        menu, _ = setup_models(days=1)
        assert Menu.objects.count() == 1

        res = auth_client.get(
            reverse('menu:menu-delete', kwargs={'pk': menu.id}))
        assert res.status_code == 200

    def test_delete(self, auth_client, mocker):
        menu, _ = setup_models(days=1)
        assert Menu.objects.count() == 1

        notify = mocker.patch('menu.views.notify_menu_deleted.delay')

        res = auth_client.post(
            reverse('menu:menu-delete', kwargs={'pk': menu.id}))

        notify.assert_called_with(menu.id)

        assert res.status_code == 302
        assert Menu.objects.count() == 1


class TestUpdateOrder:
    def test_unprotected(self, client):
        menu, order = setup_models(days=1)
        res = client.get(reverse('menu:order-update', kwargs={'pk': order.pk}))
        assert res.status_code == 200

    def test_update(self, client, mocker):
        menu, order = setup_models(days=1)
        order.sent = now()
        order.save()

        assert order.selected is None

        update = mocker.patch('menu.views.update_order.delay')

        res = client.post(
            reverse('menu:order-update', kwargs={'pk': order.pk}),
            {'selected': order.menu.options[0]})
        update.assert_called_with(order.pk)
        assert res.status_code == 302

        order.refresh_from_db()
        assert order.selected == order.menu.options[0]


def test_order_complete(auth_client, mocker):
    menu, order = setup_models(days=1)

    update = mocker.patch('menu.views.update_order.delay')

    # order with no selection
    assert order.selected is None
    res = auth_client.get(
        reverse('menu:order-complete', kwargs={'pk': order.pk}))
    assert res.status_code == 400
    update.assert_not_called()
    order.refresh_from_db()
    assert order.fulfilled is None

    # active order
    update.reset_mock()
    order.selected = order.menu.options[0]
    order.save()
    res = auth_client.get(
        reverse('menu:order-complete', kwargs={'pk': order.pk}))
    assert res.status_code == 302
    update.assert_called_with(order.pk)
    
    # complete order
    update.reset_mock()
    order.refresh_from_db()
    assert order.fulfilled is not None
    res = auth_client.get(
        reverse('menu:order-complete', kwargs={'pk': order.pk}))
    assert res.status_code == 400
    order.refresh_from_db()
    update.assert_not_called()
    assert order.fulfilled is not None
