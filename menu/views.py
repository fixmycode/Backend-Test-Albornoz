from datetime import datetime

from django.http import HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import render
from django.http import HttpResponseBadRequest
from django.utils.timezone import localtime, now
from django.utils.decorators import method_decorator
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import CreateView, UpdateView, ListView, DeleteView
from django.shortcuts import get_object_or_404

from menu.models import Order, Menu
from menu.forms import OrderForm, MenuForm
from menu.tasks import (create_orders, update_order, notify_menu_change, 
                        notify_menu_deleted)

from slack.auth import protected


@method_decorator(protected(redirect_to='/slack/login/'), name='dispatch')
class ListOrder(ListView):
    model = Order
    local_now = localtime(now())

    def get_date(self):
        try:
            d_value = self.request.GET.get('d', '')
            return datetime.strptime(d_value, '%Y%m%d').date()
        except ValueError as _:
            pass
        return self.local_now.date()

    def get_queryset(self, *args, **kwargs):
        return self.model.objects.sent(date=self.get_date())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        date = self.get_date()
        context['selected_date'] = date
        dates = self.model.objects.sent().values_list(
            'date', flat=True).distinct()
        dates = set(dates)
        dates.add(self.local_now.date())
        context['dates'] = sorted(dates)
        context['active_orders'] = self.model.objects.active(date=date)
        context['pending_orders'] = self.model.objects.pending(
            date=date).count()
        context['ready_orders'] = self.model.objects.ready(date=date)
        return context


# create menu
@method_decorator(protected, name='dispatch')
class CreateMenu(CreateView):
    model = Menu
    form_class = MenuForm

    def form_valid(self, *args, **kwargs):
        response = super(CreateMenu, self).form_valid(*args, **kwargs)
        create_orders.delay(self.object.pk)
        return response

    def form_invalid(self, *args, **kwargs):
        response = super(CreateMenu, self).form_invalid(*args, **kwargs)
        response.status_code = 400
        return response

    def get_success_url(self):
        return reverse('menu:menu-list')


# edit menu
@method_decorator(protected, name='dispatch')
class UpdateMenu(SuccessMessageMixin, UpdateView):
    model = Menu
    form_class = MenuForm
    success_message = 'Menu updated successfully!'

    def form_valid(self, *args, **kwargs):
        response = super(UpdateMenu, self).form_valid(*args, **kwargs)
        notify_menu_change.delay(self.object.pk)
        return response

    def form_invalid(self, *args, **kwargs):
        response = super(UpdateMenu, self).form_invalid(*args, **kwargs)
        response.status_code = 400
        return response

    def get_success_url(self):
        url = reverse('menu:menu-update', kwargs={'pk': self.object.pk})
        return url


# list menus
@method_decorator(protected, name='dispatch')
class ListMenu(ListView):
    queryset = Menu.objects.filter(to_be_deleted=False)


# delete menu
@method_decorator(protected, name='dispatch')
class DeleteMenu(DeleteView):
    model = Menu

    def get_context_data(self, **kwargs):
        context = super(DeleteMenu, self).get_context_data(**kwargs)
        context['order_count'] = Order.objects.active(
            menu=self.get_object()).count()
        return context

    def delete(self, request, *args, **kwargs):
        menu = self.get_object()
        menu.to_be_deleted = True
        menu.save()
        notify_menu_deleted.delay(menu.pk)
        return HttpResponseRedirect(reverse('menu:menu-list'))


# create order
class UpdateOrder(SuccessMessageMixin, UpdateView):
    model = Order
    form_class = OrderForm
    success_message = 'Order saved successfully!'

    def form_valid(self, *args, **kwargs):
        response = super(UpdateOrder, self).form_valid(*args, **kwargs)
        update_order.delay(self.object.pk)
        return response

    def form_invalid(self, *args, **kwargs):
        response = super(UpdateOrder, self).form_invalid(*args, **kwargs)
        response.status_code = 405
        return response

    def get_success_url(self):
        return reverse('menu:order-update', kwargs={'pk': self.object.pk})


# toggle order completed
@protected
def order_completed(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if not order.selected:
        return HttpResponseBadRequest(
            'you can\'t complete an order with no selection')
    if order.fulfilled:
        return HttpResponseBadRequest('you can\'t unfinalize an order')
    order.fulfilled = now()
    order.save()
    update_order.delay(order.pk)
    d_value = order.date.strftime('%Y%m%d')
    return HttpResponseRedirect(reverse('menu:order-list')+f'?d={d_value}')


def error_403(request, exception):
    return render(request, '403.html')