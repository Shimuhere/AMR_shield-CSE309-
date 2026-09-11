import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.shortcuts import redirect, render
from django.utils import timezone

from ..decorators import role_required
from ..forms import PrescriptionForm, RiskLimitsForm, SaleRecordForm
from ..models import Antibiotic, PharmacyProfile, Prescription, SaleRecord, SystemSettings
from ..utils.reporting import generate_surveillance_summary
from ..utils.risk import load_area_sales, score_area


@login_required
def dashboard_redirect(request):
    if request.user.role == 'PHARMACY': return redirect('pharmacy_dashboard')
    elif request.user.role == 'GOVERNMENT': return redirect('government_dashboard')
    return redirect('user_dashboard')


@login_required
@role_required('PHARMACY')
def pharmacy_dashboard(request):
    pharmacy_profile = PharmacyProfile.objects.filter(user=request.user).first()
    if pharmacy_profile is None:
        messages.error(request, 'Your pharmacy profile is missing. Please contact an administrator.')
        return redirect('profile_settings')

    form = SaleRecordForm(pharmacy=pharmacy_profile)
    if request.method == 'POST':
        form = SaleRecordForm(request.POST, pharmacy=pharmacy_profile)
        if form.is_valid():
            form.save()
            return redirect('pharmacy_dashboard')

    sales = SaleRecord.objects.select_related('antibiotic').filter(pharmacy=pharmacy_profile).order_by('-timestamp')
    today = timezone.now().date()
    todays_sales = sales.filter(timestamp__date=today)
    stats = {
        'total_units': sales.aggregate(total=Sum('quantity'))['total'] or 0,
        'today_units': todays_sales.aggregate(total=Sum('quantity'))['total'] or 0,
        'today_transactions': todays_sales.count(),
    }
    return render(request, 'core/dashboards/pharmacy_dashboard.html', {
        'antibiotics': Antibiotic.objects.all(), 'sales': sales[:10], 'stats': stats, 'form': form
    })


@login_required
@role_required('INDIVIDUAL')
def user_dashboard(request):
    form = PrescriptionForm(user=request.user)
    if request.method == 'POST':
        form = PrescriptionForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('user_dashboard')

    prescriptions = Prescription.objects.select_related('antibiotic').filter(user=request.user).order_by('-date')
    user_lat, user_lng = request.user.latitude or 23.8103, request.user.longitude or 90.4125

    area_sales = load_area_sales()
    thresholds = SystemSettings.load()
    antibiotics = list(Antibiotic.objects.all())

    alerts = []
    for p in prescriptions:
        risk, color = score_area(area_sales, thresholds, p.antibiotic_id, user_lat, user_lng)
        p.current_risk, p.risk_color = risk, color
        if color == 'red': alerts.append({'antibiotic': p.antibiotic.name, 'risk': risk, 'color': color})

    area_alerts = []
    for a in antibiotics:
        risk, color = score_area(area_sales, thresholds, a.id, user_lat, user_lng)
        if color in ['red', 'orange']: area_alerts.append({'medicine': a.name, 'status': risk, 'color': color})

    return render(request, 'core/dashboards/user_dashboard.html', {
        'prescriptions': prescriptions, 'alerts': alerts, 'area_alerts': area_alerts,
        'antibiotics': antibiotics, 'form': form
    })


@login_required
@role_required('GOVERNMENT')
def government_dashboard(request):
    sales_data = SaleRecord.objects.select_related('pharmacy', 'antibiotic').all()
    heatmap_points = [{'lat': s.pharmacy.latitude, 'lng': s.pharmacy.longitude, 'intensity': s.quantity, 'antibiotic': s.antibiotic.name} for s in sales_data]
    summary_report, stats = generate_surveillance_summary()
    settings = SystemSettings.load()
    return render(request, 'core/dashboards/government_dashboard.html', {
        'heatmap_points_json': json.dumps(heatmap_points), 'summary_report': summary_report, 'stats': stats, 'settings': settings,
        'patient_usage': Prescription.objects.select_related('user', 'antibiotic').all().order_by('-date'),
        'pharmacy_sales': PharmacyProfile.objects.annotate(total_units=Sum('sales__quantity'), total_transactions=Count('sales')).order_by('-total_units')
    })


@login_required
@role_required('GOVERNMENT')
def update_risk_limits(request):
    if request.method == 'POST':
        form = RiskLimitsForm(request.POST, instance=SystemSettings.load())
        if form.is_valid():
            form.save()
        else:
            for error in form.errors.values():
                messages.error(request, '; '.join(error))
    return redirect('government_dashboard')
