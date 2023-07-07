from django.contrib import admin
from users.models import CustomUser
from django.contrib.auth.admin import UserAdmin

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username','email']


admin.site.register(CustomUser,CustomUserAdmin)