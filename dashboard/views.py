"""
Dashboard views for SubmitIQ.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema


class DashboardView(APIView):
    """
    Dashboard API endpoint.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get Dashboard Data",
        description="Get dashboard information for authenticated user",
        tags=["Dashboard"]
    )
    def get(self, request):
        """
        Get dashboard data.
        """
        return Response({
            'message': 'Welcome to SubmitIQ Dashboard!',
            'user': request.user.username,
        })
