from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

@login_required
def profile_settings(request):
    user = request.user
    if request.method == 'POST':
        user.email, user.first_name, user.last_name = request.POST.get('email'), request.POST.get('first_name'), request.POST.get('last_name')
        lat, lng = request.POST.get('latitude'), request.POST.get('longitude')
        if lat and lng: user.latitude, user.longitude = float(lat), float(lng)
        user.save()
        if user.role == 'PHARMACY':
            profile = user.pharmacy_profile
            profile.name, profile.address = request.POST.get('pharmacy_name'), request.POST.get('address')
            profile.latitude, profile.longitude = user.latitude, user.longitude
            profile.save()
        return redirect('profile_settings')
    return render(request, 'core/settings/profile_settings.html')
