import pytest

from django.core.exceptions import ValidationError
from django.utils.timezone import localtime, now
from datetime import timedelta
from menu.validators import validate_list_of_strings, validate_not_past

def test_validate_not_past(settings):
    today = localtime(now()) #the present date
    yesterday = today - timedelta(days=1)
    tomorrow = today + timedelta(days=1)

    # past dates are forbidden
    with pytest.raises(ValidationError) as ex:
        validate_not_past(yesterday.date())

    # dates before the threshold are ok
    settings.NORA_THRESHOLD = max(0, today.hour + 1) #sets the threshold an hour after or 0
    validate_not_past(today.date())

    # dates after the threshold are forbidden
    with pytest.raises(ValidationError) as ex:
        settings.NORA_THRESHOLD = min(23, today.hour) #sets the threshold at the same time or 23
        validate_not_past(today.date())

    # dates in the future are ok
    validate_not_past(tomorrow.date())

def test_validate_list_of_strings():
    valid = ['a', 'b', 'c']
    list_of_numbers = [5, 4, 2]
    mixed_list = ['a', 'b', 3]
    list_with_holes = ['a', '   b  ', '    ']
    just_a_string = 'testing'
    not_a_list = {'option 1': 'chicken'}

    validate_list_of_strings(valid)

    for test in [list_of_numbers, mixed_list, list_with_holes, just_a_string, not_a_list]:
        with pytest.raises(ValidationError) as ex:
            validate_list_of_strings(test)