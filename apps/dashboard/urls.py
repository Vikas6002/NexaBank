from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('customer/', views.customer_dashboard_view, name='customer'),
    path('teller/', views.teller_dashboard_view, name='teller'),
    path('teller/accounts/', views.teller_accounts_view, name='teller-accounts'),
    path('admin/', views.admin_dashboard_view, name='admin'),
    path('admin/roles/', views.admin_roles_view, name='admin-roles'),
    path('admin/accounts/', views.admin_accounts_view, name='admin-accounts'),
    path('admin/security/', views.admin_security_view, name='admin-security'),
    path('admin/freeze/<int:account_id>/', views.toggle_freeze_account_view, name='toggle-freeze'),
    path('admin/role/<int:user_id>/', views.change_user_role_view, name='change-role'),
    path('admin/approve/<int:transaction_id>/', views.approve_transfer_view, name='approve-transfer'),
    path('admin/settings/', views.update_settings_view, name='update-settings'),
]
