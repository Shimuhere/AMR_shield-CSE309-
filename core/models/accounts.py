from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = (
        ('PHARMACY', 'Pharmacy'),
        ('INDIVIDUAL', 'Individual'),
        ('GOVERNMENT', 'Government'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='INDIVIDUAL')
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

class PharmacyProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='pharmacy_profile')
    name = models.CharField(max_length=255)
    address = models.TextField()
    latitude = models.FloatField()
    longitude = models.FloatField()

    def __str__(self):
        return self.name
