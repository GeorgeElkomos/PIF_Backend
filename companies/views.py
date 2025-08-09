from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from authentication.models import Company
from .serializers import CompanySerializer, CompanyUpdateSerializer


class CompanyDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Retrieve company info based on user role"""
        user = request.user

        if user.type == "Super_Admin":
            # List all companies
            companies = Company.objects.filter(parent_company=None) # Super Admin can see all top-level companies
            serializer = CompanySerializer(companies, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            # Return only the company of the logged-in user
            company = user.company
            serializer = CompanySerializer(company)
            return Response(serializer.data, status=status.HTTP_200_OK)


    def put(self, request):
        """Update the company info of the authenticated user"""
        company = request.user.company
        serializer = CompanyUpdateSerializer(company, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
