
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from rest_framework import status

from hospital.models import User, OtpUsers
from hospital.api.gen_otp import gen_otp
from hospital.sms_otp import send_otp_email
from rest_framework import permissions



class ResetPasswordAPI(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        username = request.data.get('username')
        gmail = request.data.get('gmail')
        otp = request.data.get('otp')
        new_password = request.data.get('new_password')
        new_password2 = request.data.get('new_password2')
        try:
            # Tìm user theo username hoặc gmail
            user = None
            if username:
                user = User.objects.filter(username=username).order_by('-user_id').first()
            elif gmail:
                user = User.objects.filter(gmail=gmail).order_by('-user_id').first()
            if user is None:
                return Response({"message": "Không tìm thấy người dùng!"}, status=status.HTTP_404_NOT_FOUND)
            if not new_password or not new_password2:
                return Response({"message": "Vui lòng nhập đầy đủ mật khẩu mới và xác nhận mật khẩu mới!"}, status=status.HTTP_400_BAD_REQUEST)
            if len(new_password) < 6:
                return Response({"message": "Mật khẩu mới phải có ít nhất 6 ký tự!"}, status=status.HTTP_400_BAD_REQUEST)
            if new_password != new_password2:
                return Response({"message": "Mật khẩu mới và xác nhận mật khẩu không khớp!"}, status=status.HTTP_400_BAD_REQUEST)
            
            # Lấy OTP mới nhất của user
            otp_obj = OtpUsers.objects.filter(user=user, otp_code=otp).order_by('-otp_created_at').first()
            if otp_obj and otp_obj.otp_created_at and timezone.now() - otp_obj.otp_created_at < timezone.timedelta(minutes=5):
                user.set_password(new_password)
                user.save()
                otp_obj.otp_code = None
                otp_obj.otp_created_at = None
                otp_obj.save()
                return Response({"message": "Đặt lại mật khẩu thành công!"}, status=status.HTTP_200_OK)
            if otp_obj:
                print("OTP trong DB:", otp_obj.otp_code, otp_obj.otp_created_at)
                print(OtpUsers.objects.filter(user=user).values_list('otp_code', 'otp_created_at'))
            else:
                print("Không tìm thấy OTP phù hợp với user và mã đã nhập.")
                print(OtpUsers.objects.filter(user=user).values_list('otp_code', 'otp_created_at'))
            print("OTP nhập:", otp)
            print("Thời gian hiện tại:", timezone.now())
            return Response({"message": "OTP không hợp lệ hoặc đã hết hạn!"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"message": f"Lỗi: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
            