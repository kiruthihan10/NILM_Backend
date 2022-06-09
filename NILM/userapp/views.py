from django.http import JsonResponse
from django.contrib.auth.models import User

from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view,permission_classes

from .serializers import *

def user(request):
    if request.method == 'GET':
        user = User.objects.all()
        response_status = status.HTTP_200_OK
    elif request.method == 'POST':
        data = request.POST
        try:
            user = User.objects.create_user(
                username = data['username'].lower(),
                password = data['password'] 
            )
            response_status = status.HTTP_201_CREATED
        except Exception:
            return JsonResponse({'Error':'Bad  Request'},status=status.HTTP_400_BAD_REQUEST)
    else:
        return JsonResponse({'Error':'Bad  Request Method'},status=status.HTTP_400_BAD_REQUEST)
    return JsonResponse(
        {'users':[UsernameSerializer(instance = instance).data for instance in user]},
        status=response_status)

@api_view(['GET'])
def authenticate(request):
    data = request.GET
    print(data)
    uname = data.get('uname')
    pw = data.get('pw')
    print(uname)
    try:
        intended_user = User.objects.get(username = uname)
        return JsonResponse({'result':intended_user.check_password(pw)})
    except User.DoesNotExist:
        return JsonResponse({'result':False}, status = status.HTTP_401_UNAUTHORIZED)


# Create your views here.
