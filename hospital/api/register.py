from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView

from hospital.serializers import RegisterSerializer
from hospital.sms_otp import send_otp_email
from hospital.api.gen_otp import gen_otp
from django.utils import timezone
from rest_framework import status


# class RegisterAPI(APIView):
#     def post(self, request):
#         serializer = RegisterSerializer(data=request.data)
#         if serializer.is_valid():
#             otp = gen_otp()
#             user = serializer.save(status=False, otp_code=otp, otp_created_at=timezone.now())
#             send_otp_email(user.gmail, otp)
#             return Response({"message": "Vui lòng nhập mã xác nhận để hoàn tất đăng ký!"}, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
from hospital.models import OtpUsers

class RegisterAPI(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            otp = gen_otp()
            user = serializer.save(status=False)
            # Tạo bản ghi OtpUsers mới
            OtpUsers.objects.create(
                user=user,
                otp_code=otp,
                otp_created_at=timezone.now()
            )
            send_otp_email(user.gmail, otp)
            return Response({"message": "Vui lòng nhập mã xác nhận để hoàn tất đăng ký!"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
