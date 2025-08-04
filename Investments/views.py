# investments/views.py
from django.shortcuts import get_object_or_404
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
from .utils import update_company_info, handle_investment_exception, build_investment_response
import pandas as pd


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

        if request.user.is_superadmin():
            investments = Investment.objects.filter(year=year, period=period)
        else:
            investments = Investment.objects.filter(year=year, period=period, created_by=request.user)

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
            update_company_info(entity, data)

            with transaction.atomic():
                investment = Investment.objects.create(
                    year=data['year'],
                    period=data['period'],
                    entity=entity,
                    asset_code=data.get('Asset_code'),
                    ownership=data['Ownership_Persentage'],
                    aquization_date=data.get('aquization_date'),
                    direct_parent=parent,
                    Ultimate_parent=data.get('Ultimate_parent'),
                    RelationShip_of_investment=data.get('RelationShip_of_investment'),
                    direct=data.get('direct', False),
                    Entity_Principal_activities=data.get('Entity_Principal_activities'),
                    created_by=request.user,
                    updated_by=request.user,
                )
                investment.full_clean()

        except Exception as e:
            return handle_investment_exception(e)

        return build_investment_response("Investment created successfully", investment, status.HTTP_201_CREATED)

    def put(self, request):
        serializer = InvestmentStructuredWriteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        entity = data['entity_obj']
        parent = data['direct_parent_obj']

        try:
            update_company_info(entity, data)

            with transaction.atomic():
                investment = get_object_or_404(
                    Investment,
                    year=data['year'],
                    period=data['period'],
                    entity=entity,
                    asset_code=data.get('Asset_code')
                )

                for attr, value in {
                    'ownership': data['Ownership_Persentage'],
                    'aquization_date': data.get('aquization_date'),
                    'direct_parent': parent,
                    'Ultimate_parent': data.get('Ultimate_parent'),
                    'RelationShip_of_investment': data.get('RelationShip_of_investment'),
                    'direct': data.get('direct', False),
                    'Entity_Principal_activities': data.get('Entity_Principal_activities'),
                    'updated_by': request.user
                }.items():
                    setattr(investment, attr, value)

                investment.full_clean()
                investment.save()

        except Exception as e:
            return handle_investment_exception(e)

        return build_investment_response("Investment updated successfully", investment, status.HTTP_200_OK)

    def delete(self, request):
        investment_id = request.query_params.get("id")
        if not investment_id:
            return Response({"error": "Investment ID is required for deletion."}, status=status.HTTP_400_BAD_REQUEST)

        investment = get_object_or_404(Investment, id=investment_id)

        if not request.user.is_superuser and investment.created_by != request.user:
            return Response(
                {"error": "You do not have permission to delete this investment."},
                status=status.HTTP_403_FORBIDDEN
            )

        investment.delete()
        return Response(
            {"message": f"Investment with ID {investment_id} deleted successfully."},
            status=status.HTTP_204_NO_CONTENT
        )


class InvestmentBulkUploadView(APIView):
    permission_classes = [IsAdminUser]

    REQUIRED_COLUMNS = [
        "Asset code", "Entity Name", "Arabic Legal Name",
        "Commercial Registration (CR) number", "MOI (700) Number ",
        "Country of incorporation", 
        # Ownership columns will be handled separately
        "Acquisition/Disposal Date\nOnly for entities acquired/disposed during 2024",
        "Direct Parent", "Ultimate Parent", 
        "Relationship of investment (Subsidiary/ Associate/ JV)",
        "Direct / In-direct", "Entity’s principal activities"
    ]

    def post(self, request):
        file = request.FILES.get('file')
        year = request.data.get('year')
        period = request.data.get('period')

        if not file or not year or not period:
            return Response(
                {"error": "File, year, and period are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Read file into DataFrame
        try:
            if file.name.endswith('.csv'):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)
        except Exception as e:
            return Response({"error": f"Failed to read file: {str(e)}"}, status=400)

        # Validate required columns
        missing_columns = []
        ownership_columns = [col for col in df.columns if col.startswith("Ownership %")]
        latest_ownership_column = sorted(ownership_columns)[-1] if ownership_columns else None

        for col in self.REQUIRED_COLUMNS:
            if col not in df.columns:
                missing_columns.append(col)

        if not latest_ownership_column:
            missing_columns.append("Latest Ownership column (e.g., 'Ownership % as at 30 Jun 2025')")

        if missing_columns:
            return Response(
                {"error": "Missing required columns", "missing_columns": missing_columns},
                status=status.HTTP_400_BAD_REQUEST
            )

        records = df.to_dict(orient='records')
        success_count = 0
        errors = []

        for idx, record in enumerate(records, start=1):
            try:
                mapped_data = {
                    "year": year,
                    "period": period,
                    "Asset_code": record.get("Asset code"),
                    "Entity_Name": record.get("Entity Name"),
                    "Arabic_entity_name": record.get("Arabic Legal Name"),
                    "CR_number": record.get("Commercial Registration (CR) number"),
                    "MOI_number": record.get("MOI (700) Number "),
                    "country_of_incorporation": record.get("Country of incorporation"),
                    "Ownership_Persentage": record.get(latest_ownership_column),
                    "aquization_date": record.get("Acquisition/Disposal Date\nOnly for entities acquired/disposed during 2024"),
                    "direct_parent_name": record.get("Direct Parent"),
                    "Ultimate_parent": record.get("Ultimate Parent"),
                    "RelationShip_of_investment": record.get("Relationship of investment (Subsidiary/ Associate/ JV)"),
                    "direct": str(record.get("Direct / In-direct")).strip().lower() == "direct",
                    "Entity_Principal_activities": record.get("Entity’s principal activities")
                }

                serializer = InvestmentStructuredWriteSerializer(data=mapped_data)
                serializer.is_valid(raise_exception=True)
                data = serializer.validated_data
                entity = data['entity_obj']
                parent = data['direct_parent_obj']

                updated_fields = []
                for field, input_key in {
                    'arabic_name': "Arabic_entity_name",
                    'cr_number': "CR_number",
                    'moi_number': "MOI_number",
                    'country_of_incorporation': "country_of_incorporation"
                }.items():
                    if getattr(entity, field) != data.get(input_key):
                        setattr(entity, field, data.get(input_key))
                        updated_fields.append(field)
                if updated_fields:
                    entity.full_clean()
                    entity.save(update_fields=updated_fields)

                with transaction.atomic():
                    investment = Investment.objects.create(
                        year=year,
                        period=period,
                        entity=entity,
                        asset_code=data.get("Asset_code"),
                        ownership=data["Ownership_Persentage"],
                        aquization_date=data.get("aquization_date"),
                        direct_parent=parent,
                        Ultimate_parent=data.get("Ultimate_parent"),
                        RelationShip_of_investment=data.get("RelationShip_of_investment"),
                        direct=data.get("direct", False),
                        Entity_Principal_activities=data.get("Entity_Principal_activities"),
                        created_by=request.user,
                        updated_by=request.user,
                    )
                    investment.full_clean()

                success_count += 1

            except (DjangoValidationError, DRFValidationError) as e:
                errors.append({
                    "row": idx,
                    "error": e.message_dict if hasattr(e, "message_dict") else str(e)
                })
            except Exception as e:
                errors.append({"row": idx, "error": str(e)})

        return Response({
            "message": "Bulk upload completed.",
            "successful_records": success_count,
            "errors": errors
        }, status=status.HTTP_200_OK if success_count else status.HTTP_400_BAD_REQUEST)

