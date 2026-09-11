from django.db.models import Sum

from ..models.clinical import SaleRecord
from ..models.settings import SystemSettings

# Degrees of latitude/longitude treated as "the surrounding area" for risk scoring.
RADIUS = 0.05


def classify(sales_count, thresholds):
    if sales_count < thresholds.low_risk_limit:
        return "Normal usage", "green"
    if sales_count <= thresholds.moderate_risk_limit:
        return "Increased usage", "yellow"
    if sales_count < thresholds.high_risk_limit:
        return "High usage", "orange"
    return "Restricted (Very High Usage)", "red"


def load_area_sales():
    """Pre-aggregate every antibiotic's sales per pharmacy location in one query.

    Risk scoring compares each location against its neighbours, so fetching the
    whole grid once is far cheaper than a per-antibiotic query round trip.
    """
    return list(
        SaleRecord.objects.values(
            'antibiotic_id', 'pharmacy__latitude', 'pharmacy__longitude'
        ).annotate(total=Sum('quantity'))
    )


def area_total(area_sales, antibiotic_id, latitude, longitude):
    return sum(
        row['total']
        for row in area_sales
        if row['antibiotic_id'] == antibiotic_id
        and abs(row['pharmacy__latitude'] - latitude) <= RADIUS
        and abs(row['pharmacy__longitude'] - longitude) <= RADIUS
    )


def score_area(area_sales, thresholds, antibiotic_id, latitude, longitude):
    return classify(area_total(area_sales, antibiotic_id, latitude, longitude), thresholds)


def get_risk_level(latitude, longitude, antibiotic):
    return score_area(load_area_sales(), SystemSettings.load(), antibiotic.id, latitude, longitude)
