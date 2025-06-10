
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated


class ChangePasswordAPI(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        new_password2 = request.data.get('new_password2')
        user = request.user
        if not user.check_password(old_password):
            return Response({"message": "Mật khẩu cũ không đúng!"}, status=status.HTTP_400_BAD_REQUEST)
        if not new_password or not new_password2:
            return Response({"message": "Vui lòng nhập đầy đủ mật khẩu mới và xác nhận mật khẩu mới!"}, status=status.HTTP_400_BAD_REQUEST)
        if new_password != new_password2:
            return Response({"message": "Mật khẩu mới và xác nhận mật khẩu không khớp!"}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        return Response({"message": "Đổi mật khẩu thành công!"}, status=status.HTTP_200_OK)
