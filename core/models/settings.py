from django.db import models

class SystemSettings(models.Model):
    low_risk_limit = models.PositiveIntegerField(default=15)
    moderate_risk_limit = models.PositiveIntegerField(default=30)
    high_risk_limit = models.PositiveIntegerField(default=100)

    class Meta:
        verbose_name_plural = "System Settings"

    def __str__(self):
        return "Global Risk Thresholds"
