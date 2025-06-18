

from rest_framework.response import Response

from rest_framework import status

from hospital.models import MedicalRecord
from hospital.serializers import  MedicalRecordDetailSerializer, MedicalRecordListSerializer
from rest_framework import  viewsets, permissions




class MedicalRecordHistoryViewAPI(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    # permission_classes = [permissions.AllowAny] 

    def get_queryset(self):
        return MedicalRecord.objects.filter(
            appointment__patient_user_id=self.request.user
        ).order_by('-appointment__appointment_day')

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return MedicalRecordDetailSerializer
        return MedicalRecordListSerializer