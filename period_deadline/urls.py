from django.urls import path
from .views import PeriodDeadlineView, ChangeUserTypeView

urlpatterns = [
    path('', PeriodDeadlineView.as_view(), name='entity'),
    path('change-user-type/', ChangeUserTypeView.as_view(), name='change-user-type'),
]
