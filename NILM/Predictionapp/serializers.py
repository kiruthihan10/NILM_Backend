from rest_framework import serializers

from .models import *

class BuildingSerializer(serializers.ModelSerializer):
    model = House
    fields = ['username', 'Mean', 'Std','appliances']

class ApplianceSerializer(serializers.ModelSerializer):
    model = Appliance
    fields = ['username', 'appliance_ID', 'appliance_Name', 'mean', 'std']