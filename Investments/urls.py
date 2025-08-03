# investments/urls.py
from django.urls import path
from .views import AdminInvestmentView

urlpatterns = [
    path('admin-investments/', AdminInvestmentView.as_view(), name='admin-investments'),
]