from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404
from authentication.models import Company
from .serializers import EntitySerializer, EntityCreateSerializer, EntityUpdateSerializer
from django.db.models import Q

class EntityView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        entity_id = request.query_params.get("id", None)
        user = request.user
        if entity_id:
            # Get single entity by ID
            if user.type == "Super_Admin":
                entity = get_object_or_404(Company, id=entity_id, parent_company__isnull=False)
            else:
                entity = get_object_or_404(Company, id=entity_id, parent_company=user.company)
            serializer = EntitySerializer(entity)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            # Existing list logic
            search = request.query_params.get('search', None)

            if user.type == "Super_Admin":
                queryset = Company.objects.filter(parent_company__isnull=False)  # all entities
            else:
                queryset = Company.objects.filter(
                    parent_company=user.company  # entities under their main company
                )

            # Apply search if provided
            if search:
                queryset = queryset.filter(
                    Q(name__icontains=search) |
                    Q(arabic_name__icontains=search) |
                    Q(cr_number__icontains=search) |
                    Q(moi_number__icontains=search) |
                    Q(country_of_incorporation__icontains=search)
                )

            serializer = EntitySerializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """Create a new entity for the admin's company."""
        if request.user.type != "Admin":
            return Response({"detail": "Not authorized"}, status=status.HTTP_403_FORBIDDEN)

        serializer = EntityCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(parent_company=request.user.company)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        """Update an existing entity."""
        if request.user.type != "Admin":
            return Response({"detail": "Not authorized"}, status=status.HTTP_403_FORBIDDEN)

        entity_id = request.data.get("id")
        entity = get_object_or_404(Company, id=entity_id, parent_company=request.user.company)

        serializer = EntityUpdateSerializer(entity, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()  # parent_company won't change because it's read-only in serializer
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        """Delete an entity."""
        if request.user.type != "Admin":
            return Response({"detail": "Not authorized"}, status=status.HTTP_403_FORBIDDEN)

        entity_id = request.data.get("id")
        entity = get_object_or_404(Company, id=entity_id, parent_company=request.user.company)
        entity.delete()

        return Response({"detail": "Entity deleted"}, status=status.HTTP_204_NO_CONTENT)

