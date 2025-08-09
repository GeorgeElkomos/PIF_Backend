from django.urls import path
from .views import EntityView

urlpatterns = [
    path('', EntityView.as_view(), name='entity'),
]
