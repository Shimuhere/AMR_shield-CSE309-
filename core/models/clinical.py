from django.db import models
from .accounts import User, PharmacyProfile

class Antibiotic(models.Model):
    name = models.CharField(max_length=255)
    group = models.CharField(max_length=255)
    category = models.CharField(max_length=255)
    
    def __str__(self):
        return self.name

class SaleRecord(models.Model):
    GENDER_CHOICES = (('M', 'Male'), ('F', 'Female'), ('O', 'Other'))
    pharmacy = models.ForeignKey(PharmacyProfile, on_delete=models.CASCADE, related_name='sales')
    antibiotic = models.ForeignKey(Antibiotic, on_delete=models.CASCADE, related_name='sales')
    quantity = models.PositiveIntegerField(default=1)
    patient_age = models.PositiveIntegerField(null=True, blank=True)
    patient_gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True)
    doctor_name = models.CharField(max_length=255, null=True, blank=True)
    prescription_reference = models.CharField(max_length=255, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.antibiotic.name} @ {self.pharmacy.name}"

class Prescription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='prescriptions')
    antibiotic = models.ForeignKey(Antibiotic, on_delete=models.CASCADE, related_name='prescriptions')
    dosage = models.PositiveIntegerField(help_text="Amount in mg", null=True, blank=True)
    frequency = models.PositiveIntegerField(help_text="Times per day", null=True, blank=True)
    duration_days = models.PositiveIntegerField(help_text="Total days", null=True, blank=True)
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Prescription for {self.user.username}"
