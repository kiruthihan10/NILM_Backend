from datetime import datetime
from email.policy import default
from django.http import JsonResponse
from django.contrib.auth.models import User

from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view,permission_classes
from rest_framework.permissions import IsAuthenticated

import datetime
import numpy as np

from .serializers import *
from .models import *
from .model_maker import wavenet_maker

HOLD_TIME = 10

def load_all_models_for_demo():

    def load_dl_models_by_string(appliance_name):
        appliance = Appliance.objects.get(appliance_Name = appliance_name)
        return wavenet_maker(middle_layers_activation=appliance.middle_layers_activation, power_on_z_score=appliance.power_on_z_score).make(appliance)
    
    names = Appliance.objects.all().values_list('appliance_Name', flat = True)
    return {name: load_dl_models_by_string(name) for name in names}

dl_models = load_all_models_for_demo()

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

def predict_check(aggregate)->bool:
    return (aggregate.count() % HOLD_TIME == 0) and (aggregate.count() != 0)

def confirm_count(aggregate) -> int:
    return max(len(aggregate) - 3**6 + 1, 0)

def appliance_predict(house:House):
    aggregate = Aggregate.objects.filter(house = house).order_by('-Date_Time')
    if not predict_check(aggregate):
        return
    appliances = Appliance.objects.filter(house = house)
    for appliance in appliances:
        model = dl_models[appliance.appliance_Name]
        Power_Consumption = np.array([
            np.array(aggregate.values_list('Power_Consumption_phase_1')),
            np.array(aggregate.values_list('Power_Consumption_phase_2')),
            np.array(aggregate.values_list('Power_Consumption_phase_3'))
            ])
        Power_Consumption = Power_Consumption.reshape(1,len(aggregate),3)
        new_predictions = np.squeeze(np.array(model((np.array(Power_Consumption)-house.Mean)/house.Std)))[0,:]
        new_predictions *= appliance.std
        print(new_predictions.shape)
        print(confirm_count(aggregate))
        for new_prediction in new_predictions[:confirm_count(aggregate)]:
            prediction_instance = Predictions(
                Prediction_ID = Predictions.objects.get(appliance = appliance, aggregate = aggregate),
                appliance = appliance,
                aggregate = aggregate,
                prediction = new_prediction,
                completed = True
            )
            prediction_instance.save()
        # new_predictions += np.array(predictions.values_list('prediction', flat = True))
        # new_predictions /= 2
        for i,new_prediction in enumerate(new_predictions[confirm_count(aggregate):]):
            prediction_id = Predictions.objects.filter(appliance = appliance, aggregate = aggregate[i])
            if len(prediction_id) != 0:
                prediction_instance = Predictions(
                    Prediction_ID = prediction_id[0].Prediction_ID,
                    appliance = appliance,
                    aggregate = aggregate[i],
                    prediction = new_prediction
                )
            else:
                prediction_instance = Predictions(
                    appliance = appliance,
                    aggregate = aggregate[i],
                    prediction = new_prediction
                )
            prediction_instance.save()

def aggregate_get(request, house):
    aggregate_instances = aggregate_between(request, house)
    serializers = AggregateSerializer(aggregate_instances)
    appliance_predict(aggregate_instances)
    return JsonResponse(serializers.data, status=status.HTTP_201_CREATED)

def aggregate_post(request, house):
    data = request.POST
    aggregate_instance = Aggregate(
        house = house,
        Power_Consumption_phase_1 = data.get('Power_Consumption_phase_1'),
        Power_Consumption_phase_2 = data.get('Power_Consumption_phase_2'),
        Power_Consumption_phase_3 = data.get('Power_Consumption_phase_3'))
    aggregate_instance.save()
    appliance_predict(house)
    serializer = AggregateSerializer(instance = aggregate_instance)
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
            if appliance in predictions_dict:
                predictions_dict[appliance.appliance_ID].append(prediction_data)
            else:
                predictions_dict[appliance.appliance_ID] = [prediction_data]
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


def test(request):
    import numpy as np
    appliance = Appliance.objects.all()[0]
    # model = dl_model_load(appliance)
    print(model)
    prediction = model.predict(np.random.normal(size=(1,10000,3)))
    return JsonResponse({'None':tuple(prediction[0].tolist())}, status = status.HTTP_200_OK)