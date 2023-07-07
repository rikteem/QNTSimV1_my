from django.shortcuts import render
from users.models import CustomUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status, generics , mixins , permissions, authentication
from users.serializers import UserDetailsSerializers
from django.http import JsonResponse
from rest_framework.permissions import IsAuthenticated
# Create your views here.


class UserSignup(APIView):

    permission_classes = []
    authentication_classes =[]
    def post(self, request):
        serilizer = UserDetailsSerializers(data = request.data)
        if serilizer.is_valid():
            serilizer.create(serilizer.validated_data)
            return JsonResponse(serilizer.validated_data)


# class GetUser(APIView):
    
#     permission_classes = [IsAuthenticated]
#     def get(self, request):
#         print('request user', request.user, request.user.id)
#         users = CustomUser.objects.all()
#         serializer = UserDetailsSerializers(users, many =True)
#         output = {}
#         # output["data"]=serializer.data
#         output["users"] = request.user
#         return JsonResponse(output, safe = False)
        