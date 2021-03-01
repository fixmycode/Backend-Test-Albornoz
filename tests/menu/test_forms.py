from menu.forms import MenuForm, OrderForm
from datetime import timedelta
from django.utils.timezone import localdate, now

class TestMenuForm:
    def valid_data(self):
        tomorrow = localdate(now()) + timedelta(days=1)
        options = ['a', 'b', 'c']

        return {'date': tomorrow, 'options': options}

    def test_valid_data(self):
        form = MenuForm(data=self.valid_data())
        assert len(form.errors) == 0

    def test_invalid_date(self):
        data = self.valid_data()
        data.update({'date': localdate(now()) - timedelta(days=1)})
        form = MenuForm(data=data)
        assert len(form.errors) == 1
        assert 'date' in form.errors

    def test_invalid_options(self):
        data = self.valid_data()
        # not just empty strings, or multiple instances of the parameter
        invalid_options = [['    ', '   ', '  '], [['  '],['a', 'b']], [['a'], ['b']]]
        for test in invalid_options:
            data.update({'options': test})
            form = MenuForm(data=data)
            form.errors
            assert len(form.errors) == 1
            assert 'options' in form.errors