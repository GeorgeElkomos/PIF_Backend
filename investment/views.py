from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from django.shortcuts import get_object_or_404

from period_deadline.models import PeriodDeadline
from .models import Investment
from authentication.models import Company
from .serializers import InvestmentCreateSerializer, InvestmentSerializer, ReportRowSerializer
from django.utils import timezone

class InvestmentView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_or_create_or_update_entity(self, user_company, entity_name, arabic_name, cr_number, moi_number, country):
        # Try find by unique entity_name under this user's company
        entity_qs = Company.objects.filter(parent_company=user_company, name=entity_name)
        if entity_qs.exists():
            entity = entity_qs.first()
            # Update entity fields with new data
            entity.arabic_name = arabic_name
            entity.cr_number = cr_number
            entity.moi_number = moi_number
            entity.country_of_incorporation = country
            entity.save()
        else:
            entity = Company.objects.create(
                parent_company=user_company,
                name=entity_name,
                arabic_name=arabic_name,
                cr_number=cr_number,
                moi_number=moi_number,
                country_of_incorporation=country,
                is_active=True,
            )
        return entity

    def _get_investments_for_user(self, user, year, time_period):
        main_company = user.company if user.company.parent_company is None else user.company.parent_company
        entities = Company.objects.filter(Q(id=main_company.id) | Q(parent_company=main_company))
        entity_names = entities.values_list('name', flat=True)
        return Investment.objects.filter(year=year, time_period__iexact=time_period, entity_name__in=entity_names)

    def post(self, request):
    
        user_company = request.user.company
        serializer = InvestmentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        entity = self._get_or_create_or_update_entity(
            user_company=user_company,
            entity_name=data['entity_name'],
            arabic_name=data.get('arabic_legal_name'),
            cr_number=data.get('commercial_registration_number'),
            moi_number=data.get('moi_number'),
            country=data.get('country_of_incorporation'),
        )

        # Create investment with entity info as strings (not FK)
        investment = Investment.objects.create(
            year=data['year'],
            time_period=data['time_period'],
            asset_code=data.get('asset_code'),
            entity_name=entity.name,
            arabic_legal_name=entity.arabic_name,
            commercial_registration_number=entity.cr_number,
            moi_number=entity.moi_number,
            country_of_incorporation=entity.country_of_incorporation,
            ownership_percentage=data.get('ownership_percentage', 0.0),
            acquisition_disposal_date=data.get('acquisition_disposal_date'),
            direct_parent=data.get('direct_parent'),
            ultimate_parent=data.get('ultimate_parent'),
            relationship_of_investment=data.get('relationship_of_investment'),
            direct_or_indirect=data.get('direct_or_indirect'),
            entities_principal_activities=data.get('entities_principal_activities'),
            created_by=request.user,
        )

        response_serializer = InvestmentCreateSerializer(investment)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def put(self, request):
        user_company = request.user.company

        investment_id = request.data.get('id')
        if not investment_id:
            return Response({"detail": "Investment id is required for update."}, status=status.HTTP_400_BAD_REQUEST)

        # Remove year and time_period if they exist in request.data to prevent update
        mutable_data = request.data.copy()  # make a mutable copy
        mutable_data.pop('year', None)
        mutable_data.pop('time_period', None)

        investment = get_object_or_404(Investment, id=investment_id)

        serializer = InvestmentCreateSerializer(investment, data=mutable_data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Entity logic unchanged ...
        if 'entity_name' in data:
            entity = self._get_or_create_or_update_entity(
                user_company=user_company,
                entity_name=data['entity_name'],
                arabic_name=data.get('arabic_legal_name'),
                cr_number=data.get('commercial_registration_number'),
                moi_number=data.get('moi_number'),
                country=data.get('country_of_incorporation'),
            )
            data['entity_name'] = entity.name
            data['arabic_legal_name'] = entity.arabic_name
            data['commercial_registration_number'] = entity.cr_number
            data['moi_number'] = entity.moi_number
            data['country_of_incorporation'] = entity.country_of_incorporation

        for attr, value in data.items():
            setattr(investment, attr, value)

        investment.updated_by = request.user
        investment.save()

        response_serializer = InvestmentCreateSerializer(investment)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
    
    def delete(self, request):
        investment_id = request.data.get('id')
        if not investment_id:
            return Response({"detail": "Investment id is required for deletion."}, status=status.HTTP_400_BAD_REQUEST)

        investment = get_object_or_404(Investment, id=investment_id)

        # Optionally, you can add permission checks here, for example:
        # if request.user.company != investment.created_by.company:
        #     return Response({"detail": "Not authorized to delete this investment."}, status=status.HTTP_403_FORBIDDEN)

        investment.delete()
        return Response({"detail": "Investment deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
    
    def get(self, request):
        user = request.user
        year = request.query_params.get('year')
        time_period = request.query_params.get('time_period')

        if not year or not time_period:
            return Response(
                {"detail": "Both 'year' and 'time_period' query parameters are required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Normalize to int and lowercase period for consistency
        year = int(year)
        time_period = time_period.lower()

        # Define the period order for reference
        period_order = ['first half', 'third quarter', 'forth quarter']

        def get_investments(y, p):
            if user.type == "SuperAdmin":
                investments_qs = Investment.objects.filter(year=y, time_period__iexact=p, is_submitted=True)
            else:
                investments_qs = self._get_investments_for_user(user, y, p)
            return investments_qs

        # Try to get investments for requested year and period
        investments = get_investments(year, time_period)

        if investments.exists():
            serializer = InvestmentSerializer(investments, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # If no data, find the previous period/year according to rules

        # Get index of current period
        try:
            current_index = period_order.index(time_period)
        except ValueError:
            return Response(
                {"detail": f"Invalid time_period value. Must be one of {period_order}."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Determine previous period and year
        if current_index == 0:
            # If first period of the year, look into last period of previous year
            prev_year = year - 1
            prev_period = period_order[-1]  # 'forth quarter'
        else:
            # Previous period in same year
            prev_year = year
            prev_period = period_order[current_index - 1]

        # Try to get investments for previous period/year
        investments_prev = get_investments(prev_year, prev_period)

        if investments_prev.exists():
            serializer = InvestmentSerializer(investments_prev, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # No data found even for previous period
        return Response({"detail": "No Data"}, status=status.HTTP_404_NOT_FOUND)
    
class InvestmentSubmitView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        year = request.data.get('year')
        time_period = request.data.get('time_period')
        investment_id = request.data.get('id', None)  # Optional investment id

        if not year and not investment_id:
            return Response({"detail": "Either 'year' and 'time_period' or 'id' is required."}, status=status.HTTP_400_BAD_REQUEST)

        if investment_id:
            # Submit single investment by id
            try:
                investment = Investment.objects.get(id=investment_id)
            except Investment.DoesNotExist:
                return Response({"detail": "Investment with given id not found."}, status=status.HTTP_404_NOT_FOUND)

            # If user is not superadmin, check company permission
            if user.type != "SuperAdmin":
                main_company = user.company if user.company.parent_company is None else user.company.parent_company
                entities = Company.objects.filter(Q(id=main_company.id) | Q(parent_company=main_company))
                entity_names = entities.values_list('name', flat=True)
                if investment.entity_name not in entity_names:
                    return Response({"detail": "Not authorized to submit this investment."}, status=status.HTTP_403_FORBIDDEN)

            # Check deadline only if year and time_period provided or fallback from investment
            deadline_year = investment.year
            deadline_period = investment.time_period.title()

            try:
                deadline_obj = PeriodDeadline.objects.get(year=deadline_year, time_period=deadline_period)
            except PeriodDeadline.DoesNotExist:
                return Response({"detail": "Submission for this period is not open yet."}, status=status.HTTP_400_BAD_REQUEST)

            if timezone.now() > deadline_obj.dead_line:
                return Response({"detail": "Submission deadline has passed."}, status=status.HTTP_400_BAD_REQUEST)

            # Submit single investment
            investment.is_submitted = True
            investment.submitted_at = timezone.now()
            investment.submitted_by = user
            investment.save()

            return Response({"detail": f"Investment {investment_id} submitted successfully."}, status=status.HTTP_200_OK)

        # Otherwise handle bulk submit for year & time_period
        if not year or not time_period:
            return Response({"detail": "Both 'year' and 'time_period' are required for bulk submit."}, status=status.HTTP_400_BAD_REQUEST)

        time_period = time_period.title()

        try:
            deadline_obj = PeriodDeadline.objects.get(year=year, time_period=time_period)
        except PeriodDeadline.DoesNotExist:
            return Response({"detail": "Submission for this period is not open yet."}, status=status.HTTP_400_BAD_REQUEST)

        if timezone.now() > deadline_obj.dead_line:
            return Response({"detail": "Submission deadline has passed."}, status=status.HTTP_400_BAD_REQUEST)

        main_company = user.company if user.company.parent_company is None else user.company.parent_company
        entities = Company.objects.filter(Q(id=main_company.id) | Q(parent_company=main_company))
        entity_names = entities.values_list('name', flat=True)

        investments = Investment.objects.filter(year=year, time_period__iexact=time_period, entity_name__in=entity_names)

        if not investments.exists():
            return Response({"detail": "No investments found for the specified year and period."}, status=status.HTTP_404_NOT_FOUND)

        investments.update(
            is_submitted=True,
            submitted_at=timezone.now(),
            submitted_by=user
        )
        return Response({"detail": f"All investments for year {year} and period '{time_period}' submitted."}, status=status.HTTP_200_OK)

class InvestmentUnsubmitView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        year = request.data.get('year')
        time_period = request.data.get('time_period')
        investment_id = request.data.get('id', None)  # Optional investment id

        if not year and not investment_id:
            return Response({"detail": "Either 'year' and 'time_period' or 'id' is required."}, status=status.HTTP_400_BAD_REQUEST)

        if investment_id:
            # Unsubmit single investment by id
            try:
                investment = Investment.objects.get(id=investment_id)
            except Investment.DoesNotExist:
                return Response({"detail": "Investment with given id not found."}, status=status.HTTP_404_NOT_FOUND)

            # Check permission for non-superadmin users
            if user.type != "SuperAdmin":
                main_company = user.company if user.company.parent_company is None else user.company.parent_company
                entities = Company.objects.filter(Q(id=main_company.id) | Q(parent_company=main_company))
                entity_names = entities.values_list('name', flat=True)
                if investment.entity_name not in entity_names:
                    return Response({"detail": "Not authorized to unsubmit this investment."}, status=status.HTTP_403_FORBIDDEN)

            # Unsubmit single investment
            investment.is_submitted = False
            investment.submitted_at = None
            investment.submitted_by = None
            investment.save()

            return Response({"detail": f"Investment {investment_id} unsubmitted successfully."}, status=status.HTTP_200_OK)

        # Otherwise handle bulk unsubmit for year & time_period
        if not year or not time_period:
            return Response({"detail": "Both 'year' and 'time_period' are required for bulk unsubmit."}, status=status.HTTP_400_BAD_REQUEST)

        time_period = time_period.title()

        main_company = user.company if user.company.parent_company is None else user.company.parent_company
        entities = Company.objects.filter(Q(id=main_company.id) | Q(parent_company=main_company))
        entity_names = entities.values_list('name', flat=True)

        investments = Investment.objects.filter(year=year, time_period__iexact=time_period, entity_name__in=entity_names)

        if not investments.exists():
            return Response({"detail": "No investments found for the specified year and period."}, status=status.HTTP_404_NOT_FOUND)

        investments.update(
            is_submitted=False,
            submitted_at=None,
            submitted_by=None
        )
        return Response({"detail": f"All investments for year {year} and period '{time_period}' unsubmitted."}, status=status.HTTP_200_OK)



PERIOD_ORDER = ['First Half', 'Third Quarter', 'Fourth Quarter']

def normalize_period_string(period_str: str) -> str:
    if not period_str:
        return None
    s = period_str.strip().lower()
    if 'first' in s and 'half' in s:
        return 'First Half'
    if 'third' in s or 'q3' in s or 'quarter 3' in s:
        return 'Third Quarter'
    if 'fourth' in s or 'q4' in s or 'quarter 4' in s or 'forth quarter' in s:
        return 'Fourth Quarter'
    if 'half' in s:
        return 'First Half'
    return None

def parse_period(period_combined: str = None, year: int = None, time_period: str = None):
    if period_combined:
        parts = period_combined.strip().rsplit(' ', 1)
        if len(parts) == 2 and parts[1].isdigit():
            year_val = int(parts[1])
            normal = normalize_period_string(parts[0])
            return year_val, normal
        import re
        m = re.search(r'(20\d{2})', period_combined)
        year_val = int(m.group(1)) if m else None
        normal = normalize_period_string(period_combined)
        return year_val, normal
    if year and time_period:
        return int(year), normalize_period_string(time_period)
    return None, None

def get_previous_period(year: int, period: str):
    if period not in PERIOD_ORDER:
        return None, None
    idx = PERIOD_ORDER.index(period)
    if idx == 0:
        return year - 1, PERIOD_ORDER[-1]
    return year, PERIOD_ORDER[idx - 1]

def _entities_under_main_company(user, company_id_override=None):
    """
    Return queryset of Company objects that represent the main company and its entities.
    If company_id_override is provided (and user is SuperAdmin), use that company as main company.
    """
    if company_id_override:
        try:
            main_company = Company.objects.get(id=company_id_override, parent_company__isnull=True)
        except Company.DoesNotExist:
            return Company.objects.none()
    else:
        if not getattr(user, "company", None):
            return Company.objects.none()
        main_company = user.company if user.company.parent_company is None else user.company.parent_company

    return Company.objects.filter(Q(id=main_company.id) | Q(parent_company=main_company))

class InvestmentReportView(APIView):
    permission_classes = [IsAuthenticated]

    monitored_fields = [
        ('entityNameArabic', 'Entity Name (Arabic)', 'entityNameArabic'),
        ('commercialRegistrationNumber', 'CR Number', 'commercialRegistrationNumber'),
        ('moiNumber', 'MOI Number', 'moiNumber'),
        ('countryOfIncorporation', 'Country', 'countryOfIncorporation'),
        ('ownershipPercentage', 'Ownership %', 'ownershipPercentage'),
        ('acquisitionDisposalDate', 'Acquisition Date', 'acquisitionDisposalDate'),
        ('directParentEntity', 'Direct Parent', 'directParentEntity'),
        ('ultimateParentEntity', 'Ultimate Parent', 'ultimateParentEntity'),
        ('investmentRelationshipType', 'Investment Type', 'investmentRelationshipType'),
        ('ownershipStructure', 'Ownership Structure', 'ownershipStructure'),
        ('principalActivities', 'Principal Activities', 'principalActivities'),
        ('currency', 'Currency', 'currency'),
    ]

    def post(self, request):
        user = request.user
        year_param = request.data.get('year')
        time_period_param = request.data.get('time_period')
        combined = request.data.get('period') or request.data.get('currentPeriod') or request.data.get('current_period')
        include_all = bool(request.data.get('include_all_companies') or request.data.get('includeAllCompanies') or False)
        company_id = request.data.get('company_id') or request.data.get('companyId')  # optional
        report_type = request.data.get('reportType') or request.data.get('report_type') or 'full-data'

        # parse period
        year, period = parse_period(combined, year_param, time_period_param)
        if not year or not period:
            return Response({"detail": "Invalid or missing period. Provide 'year' & 'time_period' or 'period' like 'First Half 2025'."}, status=status.HTTP_400_BAD_REQUEST)

        # Scope & auth
        if include_all and user.type != 'SuperAdmin':
            return Response({"detail": "Only SuperAdmin can request all companies."}, status=status.HTTP_403_FORBIDDEN)

        if user.type != 'SuperAdmin':
            # enforce user's own main company only
            entities_qs = _entities_under_main_company(user)
        else:
            # SuperAdmin: if company_id provided -> use that company; elif include_all True -> query all companies
            if company_id and not include_all:
                entities_qs = _entities_under_main_company(user, company_id_override=company_id)
            elif include_all:
                # all companies
                entities_qs = Company.objects.all()
            else:
                # default to the superadmin's own company (if set) as a scope
                entities_qs = _entities_under_main_company(user)

        entity_names = list(entities_qs.values_list('name', flat=True))

        def fetch_investments(y, p):
            qs = Investment.objects.filter(year=y, time_period__iexact=p)
            if not (include_all and user.type == 'SuperAdmin'):
                qs = qs.filter(entity_name__in=entity_names)
            return qs

        # fetch current and previous
        current_qs = fetch_investments(year, period)
        prev_year, prev_period = get_previous_period(year, period)
        prev_qs = fetch_investments(prev_year, prev_period) if prev_year and prev_period else Investment.objects.none()

        # Serialise rows
        current_rows = ReportRowSerializer(current_qs, many=True).data
        previous_rows = ReportRowSerializer(prev_qs, many=True).data

        # Helper: build map keyed by unique key: entityNameEnglish|commercialRegistrationNumber
        def key_for_row(r):
            name = (r.get('entityNameEnglish') or '').strip().lower()
            cr = (r.get('commercialRegistrationNumber') or '').strip().lower()
            return f"{name}|{cr}"

        prev_map = { key_for_row(r): r for r in previous_rows }
        curr_map = { key_for_row(r): r for r in current_rows }

        # Added: in current but not in previous
        added_keys = [k for k in curr_map.keys() if k not in prev_map]
        added_records = [curr_map[k] for k in added_keys]

        # Deleted: in previous but not in current
        deleted_keys = [k for k in prev_map.keys() if k not in curr_map]
        deleted_records = [prev_map[k] for k in deleted_keys]

        # Changes: in both, with field diffs
        changes = []
        for k in (set(curr_map.keys()) & set(prev_map.keys())):
            curr = curr_map[k]
            prev = prev_map[k]
            for field_key, label, _ in self.monitored_fields:
                # Access keys using the serializer field keys
                prev_val = prev.get(field_key)
                curr_val = curr.get(field_key)
                # normalize to string for robust comparison
                prev_str = ('' if prev_val is None else str(prev_val)).strip()
                curr_str = ('' if curr_val is None else str(curr_val)).strip()
                if prev_str != curr_str:
                    change_type = 'Modified'
                    if prev_str == '':
                        change_type = 'Added'
                    elif curr_str == '':
                        change_type = 'Removed'
                    changes.append({
                        "entityName": curr.get('entityNameEnglish') or prev.get('entityNameEnglish'),
                        "entityKey": k,
                        "fieldChanged": label,
                        "previousValue": prev_str or "(empty)",
                        "currentValue": curr_str or "(empty)",
                        "changeType": change_type
                    })

        # If current is empty but previous exists and you want fallback behavior:
        used_current_rows = current_rows
        used_current_period = f"{period} {year}"
        used_previous_rows = previous_rows
        used_previous_period = f"{prev_period} {prev_year}" if prev_period and prev_year else None

        if not current_rows and previous_rows:
            # fallback: return previous as current (as per earlier behavior)
            used_current_rows = previous_rows
            used_current_period = used_previous_period
            used_previous_rows = []
            used_previous_period = None
            # recompute added/deleted/changes for this swapped scenario:
            # if frontend expects added/deleted relative to prior-prior period, skip recompute here (we keep them empty)
            added_records = []
            deleted_records = []
            changes = []

        response = {
            "currentPeriod": used_current_period,
            "previousPeriod": used_previous_period,
            "currentData": used_current_rows,
            "previousData": used_previous_rows,
            "addedRecords": added_records,
            "deletedRecords": deleted_records,
            "changes": changes,
            "reportType": report_type,
            "generatedAt": timezone.now().isoformat(),
            "generatedBy": getattr(user, "username", None),
            "counts": {
                "current": len(used_current_rows),
                "previous": len(used_previous_rows),
                "added": len(added_records),
                "deleted": len(deleted_records),
                "changes": len(changes)
            }
        }

        if not used_current_rows:
            return Response({"detail": "No Data"}, status=status.HTTP_404_NOT_FOUND)

        return Response(response, status=status.HTTP_200_OK)
