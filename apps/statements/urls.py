from django.urls import path
from . import views

app_name = 'statements'

urlpatterns = [
    path('download/<int:account_id>/', views.download_statement_view, name='download'),
]
