from django import forms
from django.db import IntegrityError

from .models import Antibiotic, PharmacyProfile, Prescription, SaleRecord, SystemSettings, User


def resolve_antibiotic(name):
    """Look up an antibiotic by name without regard to case, creating it if new.

    Case-insensitive matching keeps "Amoxicillin" and "amoxicillin" from becoming
    two catalogue entries that split the same drug's surveillance totals.
    """
    existing = Antibiotic.objects.filter(name__iexact=name).first()
    if existing:
        return existing
    try:
        return Antibiotic.objects.create(name=name, group='Unknown', category='Uncategorized')
    except IntegrityError:
        # A concurrent request created it between the lookup and the insert.
        return Antibiotic.objects.get(name__iexact=name)


class AntibioticNameMixin(forms.ModelForm):
    antibiotic_name = forms.CharField(max_length=255)

    def clean_antibiotic_name(self):
        return self.cleaned_data['antibiotic_name'].strip()

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.antibiotic = resolve_antibiotic(self.cleaned_data['antibiotic_name'])
        if commit:
            instance.save()
        return instance


class SaleRecordForm(AntibioticNameMixin):
    class Meta:
        model = SaleRecord
        fields = ['quantity', 'patient_age', 'patient_gender', 'doctor_name', 'prescription_reference']

    def __init__(self, *args, pharmacy=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.pharmacy = pharmacy
        self.fields['quantity'].required = True
        self.fields['quantity'].min_value = 1

    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']
        if quantity < 1:
            raise forms.ValidationError('Quantity must be at least 1.')
        return quantity

    def clean_patient_age(self):
        age = self.cleaned_data.get('patient_age')
        if age is not None and age > 120:
            raise forms.ValidationError('Enter a patient age of 120 or below.')
        return age

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.pharmacy = self.pharmacy
        if commit:
            instance.save()
        return instance


class PrescriptionForm(AntibioticNameMixin):
    class Meta:
        model = Prescription
        fields = ['dosage', 'frequency', 'duration_days']

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_frequency(self):
        frequency = self.cleaned_data.get('frequency')
        if frequency is not None and frequency > 24:
            raise forms.ValidationError('Enter a frequency of 24 doses per day or below.')
        return frequency

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.user = self.user
        if commit:
            instance.save()
        return instance


class AntibioticForm(forms.ModelForm):
    class Meta:
        model = Antibiotic
        fields = ['name', 'group', 'category']

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        clashes = Antibiotic.objects.filter(name__iexact=name)
        if self.instance.pk:
            clashes = clashes.exclude(pk=self.instance.pk)
        if clashes.exists():
            raise forms.ValidationError('An antibiotic with this name already exists.')
        return name


class PharmacyProfileForm(forms.ModelForm):
    class Meta:
        model = PharmacyProfile
        fields = ['name', 'address', 'latitude', 'longitude']


class PharmacyCreateForm(PharmacyProfileForm):
    username = forms.CharField(max_length=150)
    password = forms.CharField(min_length=8, widget=forms.PasswordInput)

    field_order = ['username', 'password', 'name', 'address', 'latitude', 'longitude']

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('That username is already taken.')
        return username

    def save(self, commit=True):
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password'],
            role='PHARMACY',
        )
        profile = super().save(commit=False)
        profile.user = user
        profile.save()
        return profile


class RiskLimitsForm(forms.ModelForm):
    class Meta:
        model = SystemSettings
        fields = ['low_risk_limit', 'moderate_risk_limit', 'high_risk_limit']

    def clean(self):
        cleaned = super().clean()
        low, moderate, high = (
            cleaned.get('low_risk_limit'),
            cleaned.get('moderate_risk_limit'),
            cleaned.get('high_risk_limit'),
        )
        if None not in (low, moderate, high) and not low < moderate < high:
            raise forms.ValidationError(
                'Thresholds must increase: low must be below moderate, and moderate below high.'
            )
        return cleaned


class ProfileSettingsForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'latitude', 'longitude']


class PharmacyContactForm(forms.ModelForm):
    """The pharmacy-facing subset of the profile page; coordinates come from the user."""

    class Meta:
        model = PharmacyProfile
        fields = ['name', 'address']

    # The template names this input `pharmacy_name` to avoid clashing with the user fields.
    def add_prefix(self, field_name):
        return 'pharmacy_name' if field_name == 'name' else super().add_prefix(field_name)
