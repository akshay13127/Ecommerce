from django.db import models

# Create your models here.

from django.db import models

# Create your models here.
from django.contrib.auth.models import User
from djongo import models

class BaseProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class Employee(BaseProfile):
    position = models.CharField(max_length=100)

    def __str__(self):
        return f"Employee: {self.user.username}"


class Customer(BaseProfile):
    loyalty_points = models.IntegerField(default=0)
    birthdate = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Customer: {self.user.username}"


class Vendor(BaseProfile):
    company_name = models.CharField(max_length=255)
    gst_number = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"Vendor: {self.user.username}"
