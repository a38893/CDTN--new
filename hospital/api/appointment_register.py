from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from hospital.degree_exam_fee import  degree_exam_fee
from hospital.models import Appointment, Payment, User
from hospital.serializers import AppointmentSerializer
from rest_framework import permissions

class AppointmentAPI(APIView):
    # permission_classes = [IsAuthenticated]
    permission_classes = [permissions.AllowAny] 

    def get(self, request):
        # Lọc theo chuyên khoa
        specialty = request.GET.get('specialty')
        if specialty:
            doctors = User.objects.filter(
                role='doctor',
                status=True,
                doctor_profile__specialty__iexact=specialty 
                # không phân biệt chữ hoa chữ thường
            )
        else:
            doctors = User.objects.filter(role='doctor', status=True)
        # Tạo danh sách bác sĩ với thông tin cần thiết
        doctor_list = []
        for doctor in doctors:
            profile = getattr(doctor, 'doctor_profile', None)
            print('Doctor:', doctor.user_id, 'Profile:', profile)
            specialty_val = getattr(profile, 'specialty', None)
            degree = getattr(profile, 'degree', None)
            img_url = profile.img.url if profile and profile.img else None
            exam_fee = degree_exam_fee.get(degree, 0) 
            exam_fee_discount = int(exam_fee * 0.85) 
            doctor_info = {
                'user_id': doctor.user_id,
                'full_name': doctor.full_name,
                'specialty': specialty_val,
                'degree': degree,
                'exam_fee': exam_fee,
                'exam_fee_discount': exam_fee_discount,
                'img': img_url
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
            
            try:
                # Kiểm tra bác sĩ tồn tại và có trạng thái active
                doctor = User.objects.get(user_id=doctor_user_id, role='doctor', status=True)
                
                # Kiểm tra xem bác sĩ có lịch trùng không
                existing_appointment = Appointment.objects.filter(
                    doctor_user_id=doctor,
                    appointment_day=date,
                    appointment_time=time,
                    appointment_status__in=['confirmed', 'pending']
                ).exists()
                # Kiểm tra xem bác sĩ có lịch hẹn nào vào ngày và giờ này chưa
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
                    appointment_status='unpaid_deposit' 
                )
                Payment.objects.create(
                    appointment=appointment,
                    total_amount=30000,
                    payment_status='unpaid',  
                    payment_method=''  
                )
                
                return Response({
                    "message": "Đã đăng kí lịch hẹn, vui lòng đặt cọc để hoàn tất!",
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