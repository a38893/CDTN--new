
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated


class ChangePasswordAPI(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        user = request.user
        if not user.check_password(old_password):
            return Response({"message": "Mật khẩu cũ không đúng!"}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(new_password)
        user.save()
        return Response({"message": "Đổi mật khẩu thành công!"}, status=status.HTTP_200_OK)
