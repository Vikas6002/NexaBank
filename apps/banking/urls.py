from django.urls import path
from . import views

app_name = 'banking'

urlpatterns = [
    path('create-account/', views.create_account_view, name='create-account'),
    path('accounts/', views.account_list_view, name='account-list'),
    path('account/<int:pk>/', views.account_detail_view, name='account-detail'),
]
