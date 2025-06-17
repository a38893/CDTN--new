
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from hospital.models import User, OtpUsers
from rest_framework import status
from rest_framework import permissions





from datetime import timedelta

class VerifyOTP(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        gmail = request.data.get('gmail')
        otp = request.data.get('otp')
        try:
            user = User.objects.get(gmail=gmail)
            otp_obj = OtpUsers.objects.filter(user=user, otp_code=otp).order_by('-otp_created_at').first()
            if otp_obj and otp_obj.otp_created_at and timezone.now() - otp_obj.otp_created_at < timedelta(minutes=5):
                user.status = True
                user.save()
                otp_obj.is_verified = True
                otp_obj.otp_code = None
                otp_obj.save()
                return Response({"message": "Xác thực thành công!"}, status=status.HTTP_200_OK)
            return Response({"message": "Mã OTP không hợp lệ hoặc đã hết hạn!"}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({"message": "Người dùng không tồn tại!"}, status=status.HTTP_404_NOT_FOUND)
