from django.urls import path

from menu.views import (
    CreateMenu, ListMenu,
    UpdateMenu, UpdateOrder, DeleteMenu, ListOrder,
    order_completed
)

app_name = 'menu'
urlpatterns = [
    path('order/delete/<int:pk>', DeleteMenu.as_view(), name='menu-delete'),
    path('order/complete/<str:pk>', order_completed, name='order-complete'),
    path('menu/new/', CreateMenu.as_view(), name='menu-create'),
    path('menu/list/', ListMenu.as_view(), name='menu-list'),
    path('menu/edit/<int:pk>', UpdateMenu.as_view(), name='menu-update'),
    path('menu/<str:pk>', UpdateOrder.as_view(), name='order-update'),
    path('', ListOrder.as_view(), name='order-list')
]
