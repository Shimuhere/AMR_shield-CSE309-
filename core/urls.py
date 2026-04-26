from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.landing_page, name='landing_page'),
    path('dashboard/', views.dashboard_redirect, name='dashboard_redirect'),
    path('pharmacy/', views.pharmacy_dashboard, name='pharmacy_dashboard'),
    path('user/', views.user_dashboard, name='user_dashboard'),
    path('government/', views.government_dashboard, name='government_dashboard'),
    path('government/pharmacies/', views.pharmacy_list, name='pharmacy_list'),
    path('government/pharmacies/<int:pk>/edit/', views.pharmacy_edit, name='pharmacy_edit'),
    path('government/pharmacies/<int:pk>/delete/', views.pharmacy_delete, name='pharmacy_delete'),
    path('government/antibiotics/', views.antibiotic_list, name='antibiotic_list'),
    path('government/antibiotics/<int:pk>/edit/', views.antibiotic_edit, name='antibiotic_edit'),
    path('government/antibiotics/<int:pk>/delete/', views.antibiotic_delete, name='antibiotic_delete'),
    path('settings/', views.profile_settings, name='profile_settings'),
    path('pharmacy/api-guide/', views.api_docs, name='api_docs'),
    path('api/sales/', views.SaleRecordCreateAPIView.as_view(), name='api_sales_create'),
    path('government/export/', views.export_sales_csv, name='export_sales_csv'),
    path('government/report/full/', views.comprehensive_report, name='comprehensive_report'),
    path('government/settings/risk-limits/', views.update_risk_limits, name='update_risk_limits'),
    path('login/', auth_views.LoginView.as_view(template_name='core/auth/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]
