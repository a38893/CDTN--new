from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from hospital.models import Appointment, Payment, User
from hospital.serializers import AppointmentSerializer





class AppointmentAPI(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Lấy danh sách bác sĩ cho dropdown chọn"""
        # Lấy tất cả bác sĩ có trạng thái active
        doctors = User.objects.filter(role='doctor', status=True)
        
        # Tạo danh sách bác sĩ với thông tin cần thiết
        doctor_list = []
        for doctor in doctors:
            doctor_info = {
                'user_id': doctor.user_id,
                'full_name': doctor.full_name,
                'specialty': doctor.specialty,
                'degree': doctor.degree
            }
            doctor_list.append(doctor_info)
        
        return Response({
            "doctors": doctor_list
        }, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = AppointmentSerializer(data=request.data)
        if serializer.is_valid():
            date = serializer.validated_data['date']
            time = serializer.validated_data['time']
            doctor_user_id = serializer.validated_data['doctor_user_id']
            doctor_user = User.objects.get(user_id=doctor_user_id)
            description = serializer.validated_data.get('description', '')
            
            try:
                # Kiểm tra bác sĩ tồn tại và có trạng thái active
                doctor = User.objects.get(user_id=doctor_user_id, role='doctor', status=True)
                
                # Kiểm tra xem bác sĩ có lịch trùng không
                existing_appointment = Appointment.objects.filter(
                    doctor_user_id=doctor,
                    appointment_day=date,
                    appointment_time=time,
                    appointment_status__in=['scheduled', 'confirmed']
                ).exists()
                
                if existing_appointment:
                    return Response({
                        "message": "Bác sĩ đã có lịch hẹn vào thời gian này. Vui lòng chọn thời gian khác!"
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Tạo lịch hẹn mới
                appointment = Appointment.objects.create(
                    patient_user_id=request.user,
                    doctor_user_id=doctor,
                    appointment_day=date,
                    appointment_time=time,
                    description=description
                )
                Payment.objects.create(
                    appointment=appointment,
                    total_amount=30000,
                    payment_status='pending',  
                    # payment_method='bank_transfer'  # Phương thức thanh toán mặc định
                )
                
                return Response({
                    "message": "Đăng ký lịch hẹn thành công!",
                    "appointment_id": appointment.appointment_id,
                }, status=status.HTTP_201_CREATED)
                
            except User.DoesNotExist:
                return Response({
                    "message": "Bác sĩ không tồn tại hoặc không hoạt động!"
                }, status=status.HTTP_400_BAD_REQUEST)
                
            except ValueError as e:
                return Response({
                    "message": f"Lỗi: {str(e)}"
                }, status=status.HTTP_400_BAD_REQUEST)
                
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

