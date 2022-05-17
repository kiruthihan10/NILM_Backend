from datetime import datetime
from email.policy import default
from django.http import JsonResponse
from django.contrib.auth.models import User

from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view,permission_classes
from rest_framework.permissions import IsAuthenticated

import datetime

from .serializers import *
from .models import *

def building_get(request):
    try:
        building = House.objects.get(user = request.user)
    except House.DoesNotExist:
        return JsonResponse({'Error':'User Does Not Have House'},status = status.HTTP_204_NO_CONTENT)
    serializer = BuildingSerializer(instance = building)
    return JsonResponse(serializer.data, status = status.HTTP_200_OK)

def building_post(request):
    data = request.POST
    building = House(
        user = request.user,
        Mean = data.get('Mean'),
        Std=data.get('Std')
        )
    building.save()
    serializer = BuildingSerializer(instance = building)
    return JsonResponse(serializer.data, status = status.HTTP_201_CREATED)

@api_view(['GET','POST'])
@permission_classes((IsAuthenticated,))
def building(request):
    ## Get all the building details & Allow to Create or Update Building Detail
    if request.method == 'GET':
        return building_get(request)
    elif request.method == 'POST':
        return building_post(request)
    return JsonResponse({'Error':'Wrong Request Method'},status=status.HTTP_400_BAD_REQUEST)

def appliances_get(request):
    try:
        building = House.objects.get(user = request.user)
    except House.DoesNotExist:
        return JsonResponse({'Error':'User Does Not Have House'},status = status.HTTP_204_NO_CONTENT)
    appliances = Appliance.objects.filter(house = building)
    serilizer = ApplianceSerializer(appliances)
    return JsonResponse(serilizer.data, status = status.HTTP_200_OK)

def appliances_post(request):
    data = request.POST
    appliance = Appliance(
        appliance_name = data.get('name'),
        mean = data.get('mean'),
        std = data.get('std')
    )
    appliance.save()
    serializer = ApplianceSerializer(appliance)
    return JsonResponse(serializer.data, status = status.HTTP_201_CREATED)

@api_view(['GET','POST'])
@permission_classes((IsAuthenticated,))
def appliances(request):
    ## Get all the Appliances Detail & allow to Create Or Update Appliance Detail
    if request.method == 'GET':
        return appliances_get(request)
    elif request.method == 'POST':
        return appliances_post(request)

def appliance_get(request, appliance):
    try:
        house = House.objects.get(user = request.user)
    except House.DoesNotExist:
        return JsonResponse({'Error':'User Does Not Have House'},status = status.HTTP_204_NO_CONTENT)
    try:
        appliance = Appliance.objects.filter(appliance_Id = appliance, house = house)
    except Appliance.DoesNotExist:
        return JsonResponse({'Error':'User Does Not Have the Appliance Requested'},status = status.HTTP_204_NO_CONTENT)
    serializer = ApplianceSerializer(instance = appliance)
    return JsonResponse(serializer.data, status = status.HTTP_200_OK)  

@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def appliance(request, appliance):
    ## Get Specific Appliance Info
    if request.method == 'GET':
        return appliance_get(request, appliance)
# Create your views here.

def aggregate_between(request, house):
    data = request.GET
    start = data.get('start')
    if start is None:
        start = datetime.datetime.min
    end = data.get('end')
    if end is None:
        end = datetime.datetime.now()
    return Aggregate.objects.filter(hosue = house, Date_Time__range = (start, end))

def aggregate_get(request, house):
    aggregate_instances = aggregate_between(request, house)
    serializers = AggregateSerializer(aggregate_instances)
    return JsonResponse(serializers.data, status=status.HTTP_201_CREATED)

def aggregate_post(request, house):
    data = request.POST
    aggregate_instance = Aggregate(house = house, Power_Consumption = data.get('Power_Consumption'))
    aggregate_instance.save()
    serializer = AggregateSerializer(aggregate_instance)
    return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
    
@api_view(['GET','POST'])
@permission_classes((IsAuthenticated,))
def aggregate(request):
    house = House.objects.get(user = request.user)
    if request.method == 'GET':
        return aggregate_get(request, house)
    elif request.method == 'POST':
        return aggregate_post(request, house)    
    return JsonResponse({'Error':'Wrong Request Method'}, status = status.HTTP_400_BAD_REQUEST)

def prediction_get(request, house):
    aggregate_instances = aggregate_between(request, house)
    predictions_dict = {}
    for instance in aggregate_instances:
        predictions = Predictions.objects.filter(aggregate = instance)
        for prediction in predictions:
            prediction_data = PredictionSerializer(prediction).data
            if prediction.appliance in predictions_dict:
                predictions_dict[prediction.appliance.appliance_ID].append(prediction_data)
            else:
                predictions_dict[prediction.appliance.appliance_ID] = [prediction_data]
    return JsonResponse(predictions_dict, status = status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes((IsAuthenticated,))   
def predictions(request):
    house = House.objects.get(user = request.user)
    if request.method == 'GET':
        return prediction_get(request, house)
    return JsonResponse({'Error':'Wrong Request Method'}, status = status.HTTP_400_BAD_REQUEST)

def appliance_prediction_get(request, house, appliance):
    try:
        appliance = Appliance.objects.get(appliance_ID = appliance, house = house)
    except Appliance.DoesNotExist:
        return JsonResponse({'Error':'UnAuthorized Access'})
    aggregate_instances = aggregate_between(request, house)
    predictions = Predictions.objects.filter(aggregate = aggregate_instances)
    serializer = PredictionSerializer(predictions)
    return JsonResponse(serializer.data, status = status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))      
def appliance_predictions(request, appliance):
    house = House.objects.get(user = request.user)
    if request.method == 'GET':
        return appliance_prediction_get(request, house, appliance)
    return JsonResponse({'Error':'Wrong Request Method'}, status = status.HTTP_400_BAD_REQUEST)