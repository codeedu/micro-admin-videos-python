from django.db import models

# Create your models here.


class CategoryModel(models.Model):
    name = models.CharField(max_length=255)
