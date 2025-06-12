from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from ..models import Payment
from ..serializers import PaymentSerializer

class PaymentListAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        payments = Payment.objects.filter(appointment__patient_user_id=request.user).order_by('-payment_timestamp')
        serializer = PaymentSerializer(payments, many=True)
        return Response(serializer.data)