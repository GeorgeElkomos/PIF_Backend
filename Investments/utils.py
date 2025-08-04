# investments/views.py (top of file)
# investments/views.py
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError
from .serializers import (
    InvestmentStructuredReadSerializer,
    InvestmentStructuredWriteSerializer
)

COMPANY_UPDATE_FIELDS = {
    'arabic_name': 'Arabic_entity_name',
    'cr_number': 'CR_number',
    'moi_number': 'MOI_number',
    'country_of_incorporation': 'country_of_incorporation'
}


def update_company_info(entity, data):
    updated_fields = []
    for model_field, input_key in COMPANY_UPDATE_FIELDS.items():
        new_value = data.get(input_key)
        if getattr(entity, model_field) != new_value:
            setattr(entity, model_field, new_value)
            updated_fields.append(model_field)
    if updated_fields:
        entity.full_clean()
        entity.save(update_fields=updated_fields)


def handle_investment_exception(e):
    from django.db import IntegrityError
    if isinstance(e, (DjangoValidationError, DRFValidationError)):
        return Response(
            {'error': e.message_dict if hasattr(e, 'message_dict') else str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    elif isinstance(e, IntegrityError):
        return Response(
            {'error': 'Database error: ' + str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    return Response({'error': 'Unexpected error: ' + str(e)}, status=500)


def build_investment_response(message, investment, status_code):
    return Response({
        'message': message,
        'investment': InvestmentStructuredReadSerializer(investment).data
    }, status=status_code)
