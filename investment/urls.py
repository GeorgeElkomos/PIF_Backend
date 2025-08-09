from django.urls import path
from .views import (
    InvestmentView,
    InvestmentSubmitView,
    InvestmentUnsubmitView,
    InvestmentReportView
)
urlpatterns = [
    path('period/', InvestmentView.as_view(), name='investment-period'),
    path('submit/', InvestmentSubmitView.as_view(), name='investment-submit'),
    path('unsubmit/', InvestmentUnsubmitView.as_view(), name='investment-unsubmit'),
    path('report/', InvestmentReportView.as_view(), name='investment-report-row'),
]
