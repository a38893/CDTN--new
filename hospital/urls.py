from hospital import views
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from hospital.api.register import RegisterAPI
from hospital.api.login import LoginAPI
from hospital.api.appointment_register import AppointmentAPI
from hospital.api.appointment_view_history import  AppointmentHistoryViewAPI
from hospital.api.medical_record_view_history import MedicalRecordHistoryViewAPI
from hospital.api.verify_otp import VerifyOTP
from hospital.api.resend_otp import ResendOTP
from hospital.api.change_password import ChangePasswordAPI
from hospital.api.reset_password import ResetPasswordAPI
from hospital.api.logout import LogoutAPI
from hospital.api.update_profile import UserProfileView
from django.conf import settings
from django.conf.urls.static import static
router = DefaultRouter()

# xem lịch sử đặt lịch hẹn http://127.0.0.1:8000/api/appointments/
# hủy http://127.0.0.1:8000/api/appointments/1/cancel/
router.register(r'appointments', AppointmentHistoryViewAPI, basename='appointment')


# xem lịch sử hồ sơ y tế http://127.0.0.1:8000/api/medical-records/
router.register(r'medical-records', MedicalRecordHistoryViewAPI, basename='medical-record')
urlpatterns = [
    # đăng ký tài khoản
    path('api/register/', RegisterAPI.as_view(), name='register_api'),

    # đăng nhập
    path('api/login/', LoginAPI.as_view(), name='login_api'),
    path('api/logout/', LogoutAPI.as_view(), name='logout_api'),
    path('api/profile/', UserProfileView.as_view(), name='user_profile_api'),
    # đăng ký lịch hẹn
    path('api/appointmentregister/', AppointmentAPI.as_view(), name='appointment_api'),


    # nhập OTP với gmail và mã otp
    path('api/verify-otp/', VerifyOTP.as_view(), name='verify_otp'),

    # gửi lại OTP
    path('api/resend-otp/', ResendOTP.as_view(), name='resend_otp'),

    # đổi mật khẩu
    path('api/change-password/', ChangePasswordAPI.as_view(), name='change_password'),
    path('api/', include(router.urls)),
    # path('', home, name='home'),
    path('api/reset-password/', ResetPasswordAPI.as_view(), name='reset_password'),

    # path('pay/', views.index, name='index'),
    # path('payment/', views.payment, name='payment'),
    path('payment_ipn/', views.payment_ipn, name='payment_ipn'),
    path('payment_return/',views.payment_return, name='payment_return'),
    path('query/',views.query, name='query'),



    path('payment/<int:payment_id>/', views.payment, name='payment')
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)