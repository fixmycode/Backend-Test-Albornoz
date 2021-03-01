from django.urls import path
from .views import pre_install, post_install, logout, uninstall

app_name = 'slack'
urlpatterns = [
    path('login/', pre_install, name='login'),
    path('logout/', logout, name='logout'),
    path('auth/', post_install, name='auth'),
    path('uninstall/', uninstall, name='uninstall')
]
