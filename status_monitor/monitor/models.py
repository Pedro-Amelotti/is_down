from django.db import models

# Create your models here.
class Server(models.Model):
    name = models.CharField(max_length=255, unique=True)
    
    def __str__(self):
        return self.name

class System(models.Model):
    name = models.CharField(max_length=255, unique=True)
    url = models.URLField(max_length=200)
    server = models.ForeignKey(Server, on_delete=models.CASCADE, related_name='systems')
    
    def __str__(self):
        return self.name