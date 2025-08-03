"""
URL configuration for the auth app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RegisterView,
    LoginView,
    TokenRefreshView,
    LogoutView,
    UserProfileViewSet,
)

# Create router for viewsets
router = DefaultRouter()
router.register(r'profile', UserProfileViewSet, basename='user-profile')

app_name = 'auth'

urlpatterns = [
    # Authentication endpoints
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    
    # Include router URLs
    path('', include(router.urls)),
]
