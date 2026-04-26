from .public import landing_page
from .dashboards import dashboard_redirect, pharmacy_dashboard, user_dashboard, government_dashboard, update_risk_limits
from .management import pharmacy_list, pharmacy_edit, pharmacy_delete, antibiotic_list, antibiotic_edit, antibiotic_delete
from .profile import profile_settings
from .api import api_docs, SaleRecordCreateAPIView
from .reports import comprehensive_report, export_sales_csv
