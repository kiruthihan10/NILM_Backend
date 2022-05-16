from django.urls import path

from . import views

urlpatterns = [
    path('', views.user, name = 'index'),
    path('auth', views.authenticate, name = 'authenticate')
]
