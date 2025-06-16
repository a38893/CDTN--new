from rest_framework import permissions, generics
from hospital.models import Payment, PaymentDetail
from hospital.serializers import PaymentViewSerializer


class PaymentView(generics.ListAPIView):
    queryset = Payment.objects.all().order_by('-payment_timestamp')
    serializer_class = PaymentViewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Payment.objects.filter(appointment__patient_user_id=user)