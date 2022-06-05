from django.urls import path

from . import views

urlpatterns = [
    path('aggregate', views.aggregate, name='aggregate'),
    path('test', views.test, name='test'),
]
