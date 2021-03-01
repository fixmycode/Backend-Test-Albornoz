import pytest
from menu.models import Menu, Order
from django.utils.timezone import localtime, now
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from datetime import timedelta
from .utils import setup_models


pytestmark = pytest.mark.django_db


class TestMenuModel:
    def test_save_missing_date(self):
        with pytest.raises(IntegrityError) as exc:
            menu = Menu.objects.create(options=['a', 'b'])
    
    def test_valid_data(self):
        valid_date = localtime(now()).date() + timedelta(days=1)
        valid_options = ['a', 'b', 'c']
        menu = Menu.objects.create(date=valid_date, options=valid_options)
        menu.full_clean()

    def test_invalid_date(self):
        invalid_date = localtime(now()).date() - timedelta(days=3)
        valid_options = ['a', 'b', 'c']

        with pytest.raises(ValidationError) as exc:
            menu = Menu(date=invalid_date, options=valid_options)
            menu.full_clean()
        assert 'date' in str(exc.value)

    def test_invalid_options(self):
        valid_date = localtime(now()).date() + timedelta(days=1)
        invalid_options = [23, [], 'c']

        with pytest.raises(ValidationError) as exc:
            menu = Menu(date=valid_date, options=invalid_options)
            menu.full_clean()
        assert 'options' in str(exc.value)


class TestOrderModel:
    def test_copy_menu_date(self):
        menu, order = setup_models()
        valid_date = menu.date
        assert order.date == menu.date == valid_date
        menu.delete()
        # on_delete is a database action so we have to reload the order instance
        order.refresh_from_db()
        assert order.menu == None
        assert order.date == valid_date

    def test_reminder_text_today(self, settings):
        # sets the threshold to the next hour so we can create
        # orders for today
        settings.NORA_THRESHOLD = localtime(now()).hour + 1
        menu, order = setup_models(days=0)
        assert 'today' in order.reminder_text

    def test_menu_in_reminder_text(self):
        menu, order = setup_models()
        assert 'today' not in order.reminder_text
        for option in menu.options:
            assert option in order.reminder_text

    def test_is_expired(self, settings):
        _, order = setup_models(days=3)
        assert not order.is_expired, 'orders in the future can\'t be expired'
        settings.NORA_THRESHOLD = localtime(now()).hour
        _, order = setup_models(days=0)
        assert order.is_expired, 'orders created after the threshold should be expired'
        order.date = (localtime(now()) - timedelta(days=2)).date()
        assert order.is_expired, 'orders created in the past are expired'