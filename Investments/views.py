# investments/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from rest_framework import status
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError

from .models import Investment
from .serializers import (
    InvestmentStructuredReadSerializer,
    InvestmentStructuredWriteSerializer
)

class AdminInvestmentView(APIView):
    permission_classes = [IsAdminUser]  # ✅ Admins only

    def get(self, request):
        year = request.query_params.get('year')
        period = request.query_params.get('period')

        if not year or not period:
            return Response(
                {"detail": "year and period are required query parameters."},
                status=status.HTTP_400_BAD_REQUEST
            )

        investments = Investment.objects.filter(year=year, period=period)
        serializer = InvestmentStructuredReadSerializer(investments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = InvestmentStructuredWriteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        entity = data['entity_obj']
        parent = data['direct_parent_obj']

        try:
            # Step 1: Update company info if changed
            updated_fields = []
            for field, input_key in {
                'arabic_name': 'Arabic_entity_name',
                'cr_number': 'CR_number',
                'moi_number': 'MOI_number',
                'country_of_incorporation': 'country_of_incorporation'
            }.items():
                new_value = data.get(input_key)
                if getattr(entity, field) != new_value:
                    setattr(entity, field, new_value)
                    updated_fields.append(field)
            if updated_fields:
                entity.full_clean()
                entity.save(update_fields=updated_fields)

            # Step 2: Create or update investment inside atomic transaction
            with transaction.atomic():
                investment, created = Investment.objects.update_or_create(
                    year=data['year'],
                    period=data['period'],
                    entity=entity,
                    asset_code=data.get('Asset_code'),
                    defaults={
                        'ownership': data['Ownership_Persentage'],
                        'aquization_date': data.get('aquization_date'),
                        'direct_parent': parent,
                        'Ultimate_parent': data.get('Ultimate_parent'),
                        'RelationShip_of_investment': data.get('RelationShip_of_investment'),
                        'direct': data.get('direct', False),
                        'Entity_Principal_activities': data.get('Entity_Principal_activities'),
                    }
                )
                investment.full_clean()

        except (DjangoValidationError, DRFValidationError) as e:
            return Response(
                {'error': e.message_dict if hasattr(e, 'message_dict') else str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except IntegrityError as e:
            return Response(
                {'error': 'Database error occurred: ' + str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            return Response(
                {'error': 'Unexpected error: ' + str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        output_data = InvestmentStructuredReadSerializer(investment).data
        return Response({
            'message': 'Investment created successfully' if created else 'Investment updated successfully',
            'investment': output_data
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
