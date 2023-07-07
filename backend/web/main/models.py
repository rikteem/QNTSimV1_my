from email.policy import default
from django.db import models
from users.models import CustomUser
# Create your models here.

class Applications(models.Model):
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=1000)
    
    def __str__(self):
        return self.name

class Results(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=False)
    input = models.JSONField(default = list)
    topology = models.JSONField(default = list)
    output = models.JSONField(default = list, null = True, blank =True)
    logs = models.TextField(null = True, blank =True)
    graphs = models.JSONField(default = list,null = True, blank =True)
    app_name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)