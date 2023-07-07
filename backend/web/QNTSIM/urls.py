"""QNTSIM URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from main.views import (ApplicationList, ApplicationResult,  # ,log_view
                        PastResultsList, RunApp, stream_logs)
from rest_framework_simplejwt import views as jwt_views
from users.views import UserSignup

urlpatterns = [
    path('api/token/',jwt_views.TokenObtainPairView.as_view(),name ='token_obtain_pair'),
    path('api/token/refresh/',jwt_views.TokenRefreshView.as_view(),name ='token_refresh'),
    path('register/',UserSignup.as_view()),
    path('run/', RunApp.as_view()),
    path('stream-logs/', stream_logs, name='stream_logs'),
    # path('', include('main.urls')),
    path('admin/', admin.site.urls),    
    path('application_list/',ApplicationList.as_view()),
    path('result_list/', PastResultsList.as_view()),
    path('result/',ApplicationResult.as_view()),
    # path('logs/', log_view, name='logs')
]
