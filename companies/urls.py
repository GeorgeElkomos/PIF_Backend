from django.urls import path
from .views import CompanyDetailView

urlpatterns = [
    path('', CompanyDetailView.as_view(), name='company-detail'),
]
