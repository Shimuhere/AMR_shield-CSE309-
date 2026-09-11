from django.db.models import Avg, Count, Sum

from ..models.accounts import PharmacyProfile
from ..models.clinical import SaleRecord
from ..models.settings import SystemSettings
from .risk import load_area_sales, score_area


def generate_surveillance_summary():
    raw_data = SaleRecord.objects.values(
        'pharmacy__address', 'antibiotic__name', 'antibiotic_id', 'pharmacy__name',
        'pharmacy__latitude', 'pharmacy__longitude'
    ).annotate(total_units=Sum('quantity')).order_by('pharmacy__address', 'antibiotic__name', '-total_units')

    area_sales = load_area_sales()
    thresholds = SystemSettings.load()

    structured_summary = {}
    for entry in raw_data:
        loc = entry['pharmacy__address'].split(',')[-1].strip()
        drug = entry['antibiotic__name']

        risk, color = score_area(
            area_sales, thresholds, entry['antibiotic_id'],
            entry['pharmacy__latitude'], entry['pharmacy__longitude'],
        )

        structured_summary.setdefault(loc, {}).setdefault(drug, []).append({
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
