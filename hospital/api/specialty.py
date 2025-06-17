from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from hospital.models import  ProfileDoctor

class SpecialtyListAPI(APIView):
    def get(self, request):
        specialties = ProfileDoctor.objects.values('specialty').distinct()
        data = [
            {
                "specialty": s['specialty']
            }
            for s in specialties if s['specialty']
        ]
        return Response(data, status=status.HTTP_200_OK)