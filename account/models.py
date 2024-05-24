from django.db import models

class User(models.Model):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=255)
    password = models.CharField(max_length=128)

    