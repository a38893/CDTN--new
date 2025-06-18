from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from hospital.models import Appointment, Payment, User, ProfileDoctor, DegreeExamFee
from hospital.serializers import AppointmentSerializer
from rest_framework import permissions
from datetime import datetime, time, timedelta
from hospital.api.gen_time_slots import  is_valid_appointment_time
class AppointmentAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        specialty = request.GET.get('specialty')
        if specialty:
            doctors = User.objects.filter(
                role='doctor',
                status=True,
                doctor_profile__specialty__iexact=specialty
            )
        else:
            doctors = User.objects.filter(role='doctor', status=True)
        doctor_list = []
        for doctor in doctors:
            profile = getattr(doctor, 'doctor_profile', None)  
            if profile:
                degree_obj = profile.degree
                doctor_info = {
                    'user_id': doctor.user_id,
                    'full_name': doctor.full_name,
                    'specialty': profile.specialty,
                    'degree': degree_obj.degree_name if degree_obj else 'Chưa cập nhật',
                    'exam_fee': float(degree_obj.fee) if degree_obj else 0,
                    'img': profile.img.url if profile.img else None
                }
                doctor_list.append(doctor_info)
        return Response({
            "doctors": doctor_list
        }, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = AppointmentSerializer(data=request.data)
        if serializer.is_valid():
            date = serializer.validated_data['date']
            time_str = serializer.validated_data['time']
            if isinstance(time_str, str):
                try:
                    time_obj = datetime.strptime(time_str, "%H:%M").time()
                except Exception:
                    return Response({"message": "Định dạng giờ không hợp lệ. Đúng dạng HH:MM."}, status=status.HTTP_400_BAD_REQUEST)
            else:
                time_obj = time_str

            # Kiểm tra giờ hợp lệ
            if not is_valid_appointment_time(time_obj):
                return Response({
                    "message": "Chỉ được đặt lịch theo khung giờ cách 15 phút"
                }, status=status.HTTP_400_BAD_REQUEST)

            doctor_user_id = serializer.validated_data['doctor_user_id']
            # chỉ cho phép đặt lịch trùng khi trạng thái là chưa đặt cọc
            # còn đặt cọc rồi thì không thể đặt được cùng khung giờ bác sĩ nữa
            try:
                doctor = User.objects.get(user_id=doctor_user_id, role='doctor', status=True)
                existing_appointment = Appointment.objects.filter(
                    doctor_user_id=doctor,
                    appointment_day=date,
                    appointment_time=time_obj,
                    appointment_status__in=['confirmed', 'pending', 'full']
                ).exists()
                if existing_appointment:
                    return Response({
                        "message": "Bác sĩ đã có lịch hẹn vào thời gian này. Vui lòng chọn thời gian khác!"
                    }, status=status.HTTP_400_BAD_REQUEST)
                appointment = Appointment.objects.create(
                    patient_user_id=request.user,
                    doctor_user_id=doctor,
                    appointment_day=date,
                    appointment_time=time_obj,
                    appointment_status='unpaid_deposit' 
                )
                payment = Payment.objects.create(
                    appointment=appointment,
                    total_amount=30000,
                    payment_status='unpaid',  
                    payment_method=''  
                )
                return Response({
                    "message": "Đã đăng kí lịch hẹn, vui lòng đặt cọc để hoàn tất!",
                    "appointment_id": appointment.appointment_id,
                    "payment_id": payment.payment_id,
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