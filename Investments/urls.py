# investments/urls.py
from django.urls import path
from .views import AdminInvestmentView, InvestmentBulkUploadView

urlpatterns = [
    path('admin-investments/', AdminInvestmentView.as_view(), name='admin-investments'),
    path('admin-investments/bulk-upload/', InvestmentBulkUploadView.as_view(), name='admin-investments-bulk-upload'),
]