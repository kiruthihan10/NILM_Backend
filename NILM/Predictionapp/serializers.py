from rest_framework import serializers

from .models import *

class BuildingSerializer(serializers.ModelSerializer):
    model = House
    fields = ['username', 'Mean', 'Std','appliances']

class ApplianceSerializer(serializers.ModelSerializer):
    model = Appliance
    fields = ['username', 'appliance_ID', 'appliance_Name', 'mean', 'std']

class AggregateSerializer(serializers.ModelSerializer):
    model = Aggregate
    fields = ['Record_ID', 'Date_Time', 'Power_Consumption']

class PredictionSerializer(serializers.ModelSerializer):
    model = Predictions
    fields = ['Prediction_ID', 'Date_Time', 'appliance_name', 'appliance_id', 'prediction', 'completed']