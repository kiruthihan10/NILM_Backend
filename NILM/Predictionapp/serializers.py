from rest_framework import serializers

from .models import *

class BuildingSerializer(serializers.ModelSerializer):
    class Meta:
        model = House
        fields = ['username', 'Mean', 'Std','appliances']

class ApplianceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appliance
        fields = ['username', 'appliance_ID', 'appliance_Name', 'mean', 'std']

class AggregateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Aggregate
        fields = ['Record_ID', 'Date_Time', 'Power_Consumption_phase_1', 'Power_Consumption_phase_2', 'Power_Consumption_phase_3']

class PredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Predictions
        fields = ['Prediction_ID', 'Date_Time', 'appliance_name', 'id_appliance', 'prediction', 'completed']