from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.permissions import IsAuthenticated
from .serializers import CompanyRegistrationSerializer, UserLoginSerializer, ChangePasswordSerializer

class CompanyRegistrationView(APIView):
    """
    API endpoint for registering a company with its admin user.
    Returns an access token for authentication.
    """

    @extend_schema(
        request=CompanyRegistrationSerializer,
        responses={
            201: dict,  # Simple token response
            400: "Validation errors"
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = CompanyRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate JWT tokens for the newly created user
        refresh = RefreshToken.for_user(user)

        # Return token info only
        return Response({
            "tokens": {
                "refresh": str(refresh),
                "access": str(refresh.access_token)
            }
        }, status=status.HTTP_201_CREATED)

class UserLoginView(APIView):
    """
    API endpoint for logging in a user.
    Returns JWT tokens upon successful authentication.
    """

    @extend_schema(
        request=UserLoginSerializer,
        responses={
            200: dict,  # Tokens only
            400: "Validation errors",
            401: "Unauthorized"
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        return Response({
            "tokens": {
                "refresh": str(refresh),
                "access": str(refresh.access_token)
            }
        }, status=status.HTTP_200_OK)

class CustomTokenRefreshView(TokenRefreshView):
    """
    Custom token refresh to match token structure.
    """
    @extend_schema(
        request={"type": "object", "properties": {"refresh": {"type": "string"}}},
        responses={200: dict, 401: "Token expired/invalid"}
    )
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            # Match the same structure as login
            response.data = {
                "tokens": {
                    "access": response.data.get("access"),
                    "refresh": request.data.get("refresh")
                }
            }
        return response

class LogoutView(APIView):
    """
    Blacklists the given refresh token.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request={"type": "object", "properties": {"refresh": {"type": "string"}}},
        responses={205: "Logout successful", 400: "Invalid token"}
    )
    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"detail": "Logout successful"}, status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response({"detail": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)

class ChangePasswordView(APIView):
    """
    API endpoint for changing a user's password.
    """
    @extend_schema(
        request=ChangePasswordSerializer,
        responses={
            200: {"type": "object", "properties": {"detail": {"type": "string"}}},
            400: "Validation errors",
            401: "Unauthorized"
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "Password changed successfully."},
            status=status.HTTP_200_OK
        )

