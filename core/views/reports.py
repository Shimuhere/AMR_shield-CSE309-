import csv
from datetime import datetime
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from ..models import SaleRecord, Prescription, PharmacyProfile, SystemSettings
from ..utils.reporting import generate_surveillance_summary

@login_required
def comprehensive_report(request):
    if request.user.role != 'GOVERNMENT': return redirect('dashboard_redirect')
    summary_report, stats = generate_surveillance_summary()
    settings, _ = SystemSettings.objects.get_or_create(id=1)
    context = {
        'summary_report': summary_report, 'stats': stats,
        'patient_usage': Prescription.objects.select_related('user', 'antibiotic').all().order_by('-date'),
        'pharmacy_sales': PharmacyProfile.objects.annotate(total_units=Sum('sales__quantity'), total_transactions=Count('sales')).order_by('-total_units'),
        'settings': settings, 'report_date': datetime.now().strftime('%B %d, %Y'),
    }
    return render(request, 'core/reports/comprehensive_report.html', context)

@login_required
def export_sales_csv(request):
    if request.user.role != 'GOVERNMENT': return HttpResponse("Unauthorized", status=401)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="amr_surveillance_report.csv"'
    writer = csv.writer(response)
    writer.writerow(['Timestamp', 'Pharmacy Name', 'Location (Lat)', 'Location (Lng)', 'Antibiotic Name', 'Therapeutic Category', 'Units Sold', 'Patient Age', 'Patient Gender', 'Prescribing Physician', 'Ref Number'])
    for sale in SaleRecord.objects.select_related('pharmacy', 'antibiotic').all().order_by('-timestamp'):
        writer.writerow([sale.timestamp.strftime('%Y-%m-%d %H:%M'), sale.pharmacy.name, sale.pharmacy.latitude, sale.pharmacy.longitude, sale.antibiotic.name, sale.antibiotic.category, sale.quantity, sale.patient_age or 'N/A', sale.get_patient_gender_display() or 'N/A', sale.doctor_name or 'N/A', sale.prescription_reference or 'N/A'])
    return response
