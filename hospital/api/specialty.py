from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from hospital.models import ProfileDoctor

class SpecialtyListAPI(APIView):
    def get(self, request):
        specialties = (
            ProfileDoctor.objects
            .exclude(specialty__isnull=True)
            .exclude(specialty__exact='')
            .values_list('specialty', flat=True)
            .distinct()
            .order_by('specialty')
        )
        data = [{"specialty": s} for s in specialties]
        return Response(data, status=status.HTTP_200_OK)