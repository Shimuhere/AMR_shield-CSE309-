from ..models.clinical import SaleRecord
from ..models.settings import SystemSettings
from django.db.models import Sum

def get_risk_level(latitude, longitude, antibiotic):
    settings, _ = SystemSettings.objects.get_or_create(id=1)
    
    lat_min, lat_max = latitude - 0.05, latitude + 0.05
    lng_min, lng_max = longitude - 0.05, longitude + 0.05

    sales_count = SaleRecord.objects.filter(
        antibiotic=antibiotic,
        pharmacy__latitude__range=(lat_min, lat_max),
        pharmacy__longitude__range=(lng_min, lng_max)
    ).aggregate(total=Sum('quantity'))['total'] or 0

    if sales_count < settings.low_risk_limit: return "Normal usage", "green"
    elif settings.low_risk_limit <= sales_count <= settings.moderate_risk_limit: return "Increased usage", "yellow"
    elif settings.moderate_risk_limit < sales_count < settings.high_risk_limit: return "High usage", "orange"
    return "Restricted (Very High Usage)", "red"
