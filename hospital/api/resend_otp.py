from rest_framework.views import APIView
from django.utils import timezone
from hospital.models import User, OtpUsers
from hospital.sms_otp import send_otp_email
from hospital.api.gen_otp import *
from rest_framework.response import Response
from rest_framework import status




class ResendOTP(APIView):
    def post(self, request):
        gmail = request.data.get('gmail')
        try:
            user = User.objects.get(gmail=gmail)
            # Sinh OTP mới
            otp = gen_otp()
            otp_obj, created = OtpUsers.objects.get_or_create(user=user)
            otp_obj.otp_code = otp
            otp_obj.otp_created_at = timezone.now()
            otp_obj.save()
            send_otp_email(user.gmail, otp)
            return Response({"message": "Đã gửi lại mã OTP!"}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"message": "Người dùng không tồn tại!"}, status=status.HTTP_404_NOT_FOUND)