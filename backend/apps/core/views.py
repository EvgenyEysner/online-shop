from django.conf import settings
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class CompanyInfoView(APIView):
    """
    Öffentliche Firmenstammdaten für Impressum, AGB, Rechnungen etc.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        return Response(
            {
                "name": settings.COMPANY_NAME,
                "street": settings.COMPANY_STREET,
                "zip": settings.COMPANY_ZIP,
                "city": settings.COMPANY_CITY,
                "country": settings.COMPANY_COUNTRY,
                "tax_id": settings.COMPANY_TAX_ID,
                "email": settings.COMPANY_EMAIL,
                "phone": settings.COMPANY_PHONE,
                "managing_director": settings.COMPANY_MANAGING_DIRECTOR,
                "register_court": settings.COMPANY_REGISTER_COURT,
                "register_number": settings.COMPANY_REGISTER_NUMBER,
            }
        )
