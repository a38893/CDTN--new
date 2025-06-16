from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import status

from hospital.models import Appointment
from hospital.serializers import AppointmentHistoryViewSerializer
from rest_framework.decorators import action
from rest_framework import  viewsets, permissions, renderers






class AppointmentHistoryViewAPI(viewsets.ReadOnlyModelViewSet):
    serializer_class = AppointmentHistoryViewSerializer
    permission_classes = [permissions.AllowAny] 

    # permission_classes = [permissions.IsAuthenticated]
    renderer_classes = [renderers.JSONRenderer]
    
    def get_queryset(self):
        # Lấy lịch hẹn của người dùng hiện tại
        return Appointment.objects.select_related('doctor_user_id').filter(
            patient_user_id=self.request.user
        ).order_by('-appointment_day', '-appointment_time')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists():
            return Response(
                {"message": "Bạn chưa có lịch hẹn nào."},
                status=status.HTTP_200_OK
            )
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
            
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "message": "Lấy danh sách lịch hẹn thành công",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            # Kiểm tra xem người dùng có quyền xem lịch hẹn này không
            if instance.patient_user_id != request.user:
                return Response(
                    {"message": "Bạn không có quyền xem lịch hẹn này."},
                    status=status.HTTP_403_FORBIDDEN
                )
                
            serializer = self.get_serializer(instance)
            return Response({
                "message": "Lấy thông tin lịch hẹn thành công",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"message": "Không tìm thấy lịch hẹn."},
                status=status.HTTP_404_NOT_FOUND
            )
            
    # Hủy lịch hẹn
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        try:
            appointment = self.get_object()
            
            # Kiểm tra xem người dùng có quyền hủy lịch hẹn này không
            if appointment.patient_user_id != request.user:
                return Response(
                    {"message": "Bạn không có quyền hủy lịch hẹn này."},
                    status=status.HTTP_403_FORBIDDEN
                )
            # không hủy nếu đã hoàn thành 
            if appointment.appointment_status == 'completed':
                return Response(
                    {"message": "Lịch hẹn đã hoàn thành, không thể hủy."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Cho phép hủy các trạng thái
            appointment.appointment_status = 'cancelled'
            appointment.save()
            return Response(
                {"message": "Hủy lịch hẹn thành công"},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"message": "Không tìm thấy lịch hẹn."},
                status=status.HTTP_404_NOT_FOUND
            )