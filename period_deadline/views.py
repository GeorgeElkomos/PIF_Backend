from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import PeriodDeadline
from .serializers import PeriodDeadlineSerializer
from authentication.models import User  # Adjust import according to your project structure

class PeriodDeadlineView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        user = request.user
        if user.type != "SuperAdmin":
            return Response({"detail": "Not authorized"}, status=status.HTTP_403_FORBIDDEN)

        year = request.data.get('year')
        time_period = request.data.get('time_period')

        # Try to get existing instance
        try:
            instance = PeriodDeadline.objects.get(year=year, time_period=time_period)
        except PeriodDeadline.DoesNotExist:
            instance = None

        serializer = PeriodDeadlineSerializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        status_code = status.HTTP_200_OK if instance else status.HTTP_201_CREATED
        return Response(serializer.data, status=status_code)

    def get(self, request):
        # Get filter params
        year_gte = request.query_params.get('year_gte')
        deadline_gte = request.query_params.get('deadline_gte')

        queryset = PeriodDeadline.objects.all()

        # Apply filters if provided
        filters = Q()
        if year_gte:
            filters &= Q(year__gte=int(year_gte))
        if deadline_gte:
            filters &= Q(dead_line__gte=deadline_gte)

        queryset = queryset.filter(filters)

        serializer = PeriodDeadlineSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)



class ChangeUserTypeView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        user_id = request.data.get("user_id")
        new_type = request.data.get("type")

        if not user_id or not new_type:
            return Response(
                {"detail": "Both user_id and type fields are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate new_type value
        valid_types = ['SuperAdmin', 'Admin', 'User']
        if new_type not in valid_types:
            return Response(
                {"detail": f"Invalid type. Must be one of {valid_types}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = get_object_or_404(User, id=user_id)
        user.type = new_type
        user.save()

        return Response(
            {"detail": f"User type updated to '{new_type}' successfully."},
            status=status.HTTP_200_OK,
        )
