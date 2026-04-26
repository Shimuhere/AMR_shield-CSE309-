from django.shortcuts import render, redirect
from .dashboards import dashboard_redirect

def landing_page(request):
    if request.user.is_authenticated:
        return dashboard_redirect(request)
    return render(request, 'landing.html')
