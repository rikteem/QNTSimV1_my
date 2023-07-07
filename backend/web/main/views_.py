from django.http import JsonResponse
from rest_framework.views import APIView
from .simulator.topo_funcs import *
import importlib, qntsim

class RunAPP(APIView):
    def post(self, request):
        importlib.reload(qntsim)
        app_name = request.data.get('application')
        topology = request.data.get('topology')
        app_settings = request.data.get('app_settings')
        response = create_response(**app_settings, app_name=app_name, network_config=topology)
        
        return JsonResponse(response, safe=False)