from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from ..forms import PharmacyContactForm, ProfileSettingsForm
from ..models import PharmacyProfile


@login_required
def profile_settings(request):
    user = request.user
    profile = PharmacyProfile.objects.filter(user=user).first() if user.role == 'PHARMACY' else None

    user_form = ProfileSettingsForm(instance=user)
    pharmacy_form = PharmacyContactForm(instance=profile) if profile else None

    if request.method == 'POST':
        user_form = ProfileSettingsForm(request.POST, instance=user)
        forms = [user_form]
        if profile:
            pharmacy_form = PharmacyContactForm(request.POST, instance=profile)
            forms.append(pharmacy_form)

        if all(f.is_valid() for f in forms):
            user = user_form.save()
            if profile:
                pharmacy = pharmacy_form.save(commit=False)
                # Keep the pharmacy pinned to the account's coordinates, but never
                # overwrite a real location with a blank one.
                if user.latitude is not None and user.longitude is not None:
                    pharmacy.latitude, pharmacy.longitude = user.latitude, user.longitude
                pharmacy.save()
            messages.success(request, 'Your settings have been saved.')
            return redirect('profile_settings')

    return render(request, 'core/settings/profile_settings.html', {
        'user_form': user_form, 'pharmacy_form': pharmacy_form
    })
