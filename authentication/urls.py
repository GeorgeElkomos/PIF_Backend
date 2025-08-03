"""
URL configuration for the auth app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    LoginView,
    TokenRefreshView,
    LogoutView,
    UserProfileViewSet,
)
from .views_new import (
    CompanyRegisterView,
    CompanyApprovalViewSet,
    CompanyUserManagementViewSet,
)

# Create router for viewsets
router = DefaultRouter()
router.register(r'profile', UserProfileViewSet, basename='user-profile')
router.register(r'company-approvals', CompanyApprovalViewSet, basename='company-approvals')
router.register(r'company-users', CompanyUserManagementViewSet, basename='company-users')

app_name = 'authentication'

urlpatterns = [
    # Authentication endpoints
    path('register/', CompanyRegisterView.as_view(), name='company-register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    
    # Include router URLs
    path('', include(router.urls)),
]
