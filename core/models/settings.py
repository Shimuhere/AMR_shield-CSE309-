from django.db import models

class SystemSettings(models.Model):
    SINGLETON_ID = 1

    low_risk_limit = models.PositiveIntegerField(default=15)
    moderate_risk_limit = models.PositiveIntegerField(default=30)
    high_risk_limit = models.PositiveIntegerField(default=100)

    class Meta:
        verbose_name_plural = "System Settings"

    @classmethod
    def load(cls):
        return cls.objects.get_or_create(id=cls.SINGLETON_ID)[0]

    def save(self, *args, **kwargs):
        self.id = self.SINGLETON_ID
        super().save(*args, **kwargs)

    def __str__(self):
        return "Global Risk Thresholds"
