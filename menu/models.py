from uuid import uuid4
from datetime import datetime, time

from django.db import models
from django.conf import settings
from django.template.loader import get_template
from django.utils import timezone

from menu.validators import validate_not_past, validate_list_of_strings


class Menu(models.Model):
    """Represents a list of choices of meals for a defined date
    """
    date = models.DateField(validators=[validate_not_past])
    options = models.JSONField(validators=[validate_list_of_strings])
    sent = models.DateTimeField(null=True, blank=True)
    to_be_deleted = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        super(Menu, self).save(*args, **kwargs)
        self.orders.update(date=self.date)


class OrderManager(models.Manager):
    """Defines the states that the order can take with filters"""
    def sent(self, **kwargs):
        return self.filter(sent__isnull=False, **kwargs)

    def pending(self, **kwargs):
        return self.sent().filter(
            fulfilled__isnull=True, selected__isnull=True, **kwargs)

    def active(self, **kwargs):
        return self.sent().filter(
            fulfilled__isnull=True, selected__isnull=False, **kwargs)

    def ready(self, **kwargs):
        return self.sent().filter(
            fulfilled__isnull=False, selected__isnull=False, **kwargs)


class Order(models.Model):
    """Represents the relationship between an employee and a particular menu.
    It also stores information about the task of sending the information to
    the user."""

    id = models.UUIDField(default=uuid4, primary_key=True)
    employee_slack_id = models.CharField(max_length=256)
    employee_real_name = models.CharField(max_length=256)
    employee_channel = models.CharField(max_length=256, null=True)
    menu = models.ForeignKey(Menu,
                             related_name='orders',
                             null=True,
                             on_delete=models.SET_NULL)
    date = models.DateField()
    selected = models.CharField(max_length=256, null=True)
    notes = models.CharField(max_length=256, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(null=True, auto_now=True)
    sent = models.DateTimeField(null=True)
    fulfilled = models.DateTimeField(null=True)
    ts = models.CharField(max_length=256, null=True)

    class Meta:
        ordering = ['date', 'created']

    objects = OrderManager()
    _today = timezone.localtime(timezone.now())

    def save(self, *args, **kwargs):
        if self.menu:
            self.date = self.menu.date
        super(Order, self).save(*args, **kwargs)

    @property
    def reminder_text(self):
        template = get_template('order_message.txt')
        return template.render({
            'order': self,
            'today': self._today.date(),
            'nora_url': settings.NORA_URL
        })

    @property
    def valid_until(self):
        cut_time = time(settings.NORA_THRESHOLD, 0)
        return timezone.make_aware(datetime.combine(self.date, cut_time))

    @property
    def is_expired(self):
        return (self.date < self._today.date() or
                self._today >= self.valid_until or
                self.fulfilled is not None)
