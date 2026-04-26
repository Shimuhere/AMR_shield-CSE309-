import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.utils import timezone
from ..models import SaleRecord, Antibiotic, Prescription, PharmacyProfile, SystemSettings
from ..utils.risk import get_risk_level
from ..utils.reporting import generate_surveillance_summary

@login_required
def dashboard_redirect(request):
    if request.user.role == 'PHARMACY': return redirect('pharmacy_dashboard')
    elif request.user.role == 'GOVERNMENT': return redirect('government_dashboard')
    return redirect('user_dashboard')

@login_required
def pharmacy_dashboard(request):
    if request.user.role != 'PHARMACY': return redirect('dashboard_redirect')
    pharmacy_profile = request.user.pharmacy_profile
    if request.method == 'POST':
        antibiotic, _ = Antibiotic.objects.get_or_create(
            name=request.POST.get('antibiotic_name'),
            defaults={'group': 'Unknown', 'category': 'Uncategorized'}
        )
        SaleRecord.objects.create(
            pharmacy=pharmacy_profile, antibiotic=antibiotic,
            quantity=request.POST.get('quantity'),
            patient_age=request.POST.get('patient_age') or None,
            patient_gender=request.POST.get('patient_gender'),
            doctor_name=request.POST.get('doctor_name'),
            prescription_reference=request.POST.get('prescription_reference')
        )
        return redirect('pharmacy_dashboard')
    
    sales = SaleRecord.objects.filter(pharmacy=pharmacy_profile).order_by('-timestamp')
    today = timezone.now().date()
    stats = {
        'total_units': sales.aggregate(total=Sum('quantity'))['total'] or 0,
        'today_units': sales.filter(timestamp__date=today).aggregate(total=Sum('quantity'))['total'] or 0,
        'today_transactions': sales.filter(timestamp__date=today).count(),
        'unique_patients': sales.values('patient_age', 'patient_gender').distinct().count()
    }
    return render(request, 'core/dashboards/pharmacy_dashboard.html', {
        'antibiotics': Antibiotic.objects.all(), 'sales': sales[:10], 'stats': stats
    })

@login_required
def user_dashboard(request):
    if request.user.role != 'INDIVIDUAL': return redirect('dashboard_redirect')
    if request.method == 'POST':
        antibiotic, _ = Antibiotic.objects.get_or_create(
            name=request.POST.get('antibiotic_name'),
            defaults={'group': 'Unknown', 'category': 'Uncategorized'}
        )
        Prescription.objects.create(
            user=request.user, antibiotic=antibiotic,
            dosage=int(request.POST.get('dosage')) if request.POST.get('dosage') else None,
            frequency=int(request.POST.get('frequency')) if request.POST.get('frequency') else None,
            duration_days=int(request.POST.get('duration_days')) if request.POST.get('duration_days') else None
        )
        return redirect('user_dashboard')

    prescriptions = Prescription.objects.filter(user=request.user).order_by('-date')
    user_lat, user_lng = request.user.latitude or 23.8103, request.user.longitude or 90.4125
    alerts = []
    for p in prescriptions:
        risk, color = get_risk_level(user_lat, user_lng, p.antibiotic)
        p.current_risk, p.risk_color = risk, color
        if color == 'red': alerts.append({'antibiotic': p.antibiotic.name, 'risk': risk, 'color': color})
    
    area_alerts = []
    for a in Antibiotic.objects.all():
        risk, color = get_risk_level(user_lat, user_lng, a)
        if color in ['red', 'orange']: area_alerts.append({'medicine': a.name, 'status': risk, 'color': color})

    return render(request, 'core/dashboards/user_dashboard.html', {
        'prescriptions': prescriptions, 'alerts': alerts, 'area_alerts': area_alerts, 'antibiotics': Antibiotic.objects.all()
    })

@login_required
def government_dashboard(request):
    if request.user.role != 'GOVERNMENT': return redirect('dashboard_redirect')
    sales_data = SaleRecord.objects.select_related('pharmacy', 'antibiotic').all()
    heatmap_points = [{'lat': s.pharmacy.latitude, 'lng': s.pharmacy.longitude, 'intensity': s.quantity, 'antibiotic': s.antibiotic.name} for s in sales_data]
    summary_report, stats = generate_surveillance_summary()
    settings, _ = SystemSettings.objects.get_or_create(id=1)
    return render(request, 'core/dashboards/government_dashboard.html', {
        'heatmap_points_json': json.dumps(heatmap_points), 'summary_report': summary_report, 'stats': stats, 'settings': settings,
        'patient_usage': Prescription.objects.select_related('user', 'antibiotic').all().order_by('-date'),
        'pharmacy_sales': PharmacyProfile.objects.annotate(total_units=Sum('sales__quantity'), total_transactions=Count('sales')).order_by('-total_units')
    })

@login_required
def update_risk_limits(request):
    if request.user.role != 'GOVERNMENT': return redirect('dashboard_redirect')
    if request.method == 'POST':
        settings, _ = SystemSettings.objects.get_or_create(id=1)
        settings.low_risk_limit = request.POST.get('low_risk_limit')
        settings.moderate_risk_limit = request.POST.get('moderate_risk_limit')
        settings.high_risk_limit = request.POST.get('high_risk_limit')
        settings.save()
    return redirect('government_dashboard')
