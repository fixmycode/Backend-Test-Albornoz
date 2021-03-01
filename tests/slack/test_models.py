import pytest
from slack.models import SlackIdentity

pytestmark = pytest.mark.django_db


class TestSlackIdentity:
    def test_singleton(self):
        first = SlackIdentity(user_id='a', team_id='b', access_token='123')
        first.save()

        assert first.pk == 1
        assert SlackIdentity.objects.count() == 1

        second = SlackIdentity(user_id='c', team_id='d', access_token='456')
        second.save()

        assert second.pk == 1
        assert SlackIdentity.objects.count() == 1

        assert first == second

        third = SlackIdentity.objects.create(
            user_id='e', team_id='f', access_token='789')

        assert second == third
