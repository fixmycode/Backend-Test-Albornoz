from django.core.exceptions import ValidationError
from django.utils.timezone import localtime, now
from django.conf import settings


def validate_not_past(value):
    """Validates that the given date is not in the past"""
    local_now = localtime(now())
    if value < local_now.date():
        raise ValidationError('you can\'t create menus for a past date')
    if value == local_now.date() and local_now.hour >= settings.NORA_THRESHOLD:
        raise ValidationError(
            'you can\'t create a menu for today now, it\'s too late!')


def validate_list_of_strings(value):
    """Validates that the given value is a list and its
    elements are all strings"""
    if not isinstance(value, list):
        raise ValidationError('it\'s not a list!')
    for elem in value:
        if not isinstance(elem, str):
            raise ValidationError('it has to contain strings!')
        if elem.strip() == '':
            raise ValidationError('it contains empty strings!')
