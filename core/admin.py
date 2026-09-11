from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Antibiotic, PharmacyProfile, Prescription, SaleRecord, SystemSettings, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'role', 'email', 'is_staff', 'is_superuser']
    list_filter = ['role', 'is_staff', 'is_superuser', 'is_active']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('AMR Shield', {'fields': ('role', 'latitude', 'longitude')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('AMR Shield', {'fields': ('role',)}),
    )


@admin.register(PharmacyProfile)
class PharmacyProfileAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'address', 'latitude', 'longitude']
    search_fields = ['name', 'address']


@admin.register(Antibiotic)
class AntibioticAdmin(admin.ModelAdmin):
    list_display = ['name', 'group', 'category']
    list_filter = ['group', 'category']
    search_fields = ['name', 'group', 'category']


@admin.register(SaleRecord)
class SaleRecordAdmin(admin.ModelAdmin):
    list_display = ['antibiotic', 'pharmacy', 'quantity', 'patient_age', 'patient_gender', 'timestamp']
    list_filter = ['antibiotic', 'pharmacy', 'patient_gender']
    date_hierarchy = 'timestamp'
    list_select_related = ['antibiotic', 'pharmacy']


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'antibiotic', 'dosage', 'frequency', 'duration_days', 'date']
    list_filter = ['antibiotic']
    list_select_related = ['user', 'antibiotic']


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'low_risk_limit', 'moderate_risk_limit', 'high_risk_limit']

    def has_add_permission(self, request):
        # A single global row backs every risk calculation.
        return not SystemSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
