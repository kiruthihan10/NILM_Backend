from django.urls import path

from . import views

urlpatterns = [
    path('building', views.building, name='building'),
    path('appliance', views.appliances, name='appliance'),
    path('appliance/<int:appliance_id>', views.appliance, name='appliance_detail'),
    path('predictions', views.predictions, name='predictions'),
    path('predictions/<int:appliance>', views.appliance_predictions, name='appliance_predictions'),
    path('aggregate', views.aggregate, name='aggregate'),
]
