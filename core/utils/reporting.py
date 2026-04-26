from django.db.models import Sum, Count, Avg
from ..models.accounts import PharmacyProfile
from ..models.clinical import SaleRecord, Antibiotic
from .risk import get_risk_level

def generate_surveillance_summary():
    raw_data = SaleRecord.objects.values(
        'pharmacy__address', 'antibiotic__name', 'pharmacy__name',
        'pharmacy__latitude', 'pharmacy__longitude'
    ).annotate(total_units=Sum('quantity')).order_by('pharmacy__address', 'antibiotic__name', '-total_units')

    structured_summary = {}
    for entry in raw_data:
        loc = entry['pharmacy__address'].split(',')[-1].strip()
        drug = entry['antibiotic__name']
        
        if loc not in structured_summary: structured_summary[loc] = {}
        if drug not in structured_summary[loc]: structured_summary[loc][drug] = []
            
        antibiotic = Antibiotic.objects.get(name=drug)
        risk, color = get_risk_level(entry['pharmacy__latitude'], entry['pharmacy__longitude'], antibiotic)
        
        structured_summary[loc][drug].append({
            'pharmacy': entry['pharmacy__name'], 'units': entry['total_units'],
            'risk_level': risk, 'color': color
        })

    stats = {
        'total_units': SaleRecord.objects.aggregate(total=Sum('quantity'))['total'] or 0,
        'active_pharmacies': PharmacyProfile.objects.count(),
        'avg_patient_age': SaleRecord.objects.aggregate(avg=Avg('patient_age'))['avg'] or 0,
        'gender_distribution': list(SaleRecord.objects.values('patient_gender').annotate(count=Count('id'))),
        'antibiotic_category_distribution': list(SaleRecord.objects.values('antibiotic__category').annotate(count=Sum('quantity')))
    }
    return structured_summary, stats
