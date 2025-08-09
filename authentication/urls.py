from django.urls import path
from .views import (
    CompanyRegistrationView,
    UserLoginView,
    CustomTokenRefreshView,
    LogoutView,
    ChangePasswordView
)

urlpatterns = [
    path('register/', CompanyRegistrationView.as_view(), name='company-register'),
    path('login/', UserLoginView.as_view(), name='user-login'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token-refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
]
