import datetime
from django.utils import timezone
from datetime import time
from rest_framework import serializers
from .models import PatientTest, Prescription, User,Appointment, MedicalRecord, Payment, PaymentDetail
from django.contrib.auth.hashers import make_password


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['user_id', 'full_name', 'username',  'gender', 'phone', 'address', 'birth_day']
        read_only_fields = ['user_id', 'usename']
        extra_kwargs = {
            'password': {'write_only': True},
            'is_superuser': {'default': False}  
        }

class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['full_name', 'username',  'gender', 'phone', 'address', 'birth_day']
        read_only_fields = [ 'usename']
        extra_kwargs = {
            'password': {'write_only': True},
            'is_superuser': {'default': False}  }
# 'username', 'full_name', 'gender', 'phone', 'address', 'birth_day'

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, label="Xác nhận mật khẩu")
    class Meta:
        model = User
        fields = ['username', 'password','password2', 'full_name', 'gender', 'phone', 'address', 'birth_day', 'gmail']
        extra_kwargs = {'password': {'write_only': True}}
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError("Mật khẩu và xác nhận mật khẩu không khớp!")
        return attrs
    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Tên đăng nhập đã tồn tại!")
        return value

    def validate_birth_day(self, value):
        if isinstance(value, str):
            try:
                value = datetime.strptime(value, '%Y-%m-%d').date()
            except ValueError:
                raise serializers.ValidationError("Ngày sinh phải có định dạng YYYY-MM-DD!(ví dụ: 2023-10-01: Ngày 01 tháng 10 năm 2023)")
        if not isinstance(value, datetime.date):
            raise serializers.ValidationError("Ngày sinh phải là một ngày hợp lệ!")
        if value.year < 1900:
            raise serializers.ValidationError("Ngày sinh không thể trước năm 1900!")
        if value > datetime.date.today():
            raise serializers.ValidationError("Ngày sinh không thể là ngày trong tương lai!")
        if value > datetime.datetime.now().date():
            raise serializers.ValidationError("Ngày sinh không thể là tương lai!")
        return value

    def create(self, validated_data):
        validated_data.pop('password2', None) 
        validated_data['password'] = make_password(validated_data['password'])
        validated_data['status'] = False
        return User.objects.create(**validated_data)

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})

class AppointmentSerializer(serializers.Serializer):
    date = serializers.DateField(required=True)
    time = serializers.TimeField(required=True)
    doctor_user_id = serializers.IntegerField(required=True)
    # description = serializers.CharField(required=False, allow_blank=True)
    
    def validate_date(self, value):
        """
        Kiểm tra ngày hẹn không được là ngày trong quá khứ
        """
        today = timezone.now().date()
        if value < today:
            raise serializers.ValidationError("Ngày hẹn không thể là ngày trong quá khứ!")
        return value
    
    def validate_time(self, value):
        """
        Kiểm tra giờ hẹn phải trong giờ làm việc (8:00 - 17:00)
        """
        # Chuyển đổi thành datetime.time để so sánh
        start_time = time(8, 0)  # 8:00 AM
        end_time = time(17, 0)   # 5:00 PM
        
        if value < start_time or value > end_time:
            raise serializers.ValidationError("Giờ hẹn phải trong khoảng 8:00 - 17:00!")
        return value
    
    def validate(self, data):
        """
        Kiểm tra nếu ngày hẹn là hôm nay, giờ hẹn phải là tương lai
        """
        date = data.get('date')
        appointment_time = data.get('time')
        
        if date == timezone.now().date():
            current_time = timezone.now().time()
            if appointment_time <= current_time:
                raise serializers.ValidationError({"time": "Giờ hẹn phải là thời gian trong tương lai!"})
        
        return data

class AppointmentHistoryViewSerializer(serializers.ModelSerializer):
    patient = UserSerializer(source='patient_user_id', read_only = True)
    doctor = UserSerializer(source='doctor_user_id', read_only = True)

    class Meta:
        model = Appointment
        fields = ['appointment_id', 'patient', 'doctor', 'appointment_day', 'appointment_time', 'appointment_status', 'description']
        
class PatientTestSerializer(serializers.ModelSerializer):
    test_name = serializers.CharField(source='test.test_name', read_only=True)
    test_id = serializers.IntegerField(source='test.test_id', read_only=True)

    class Meta:
        model = PatientTest
        fields = ['patient_test_id', 'test_id', 'test_name', 'result', 'test_date', 'status']
class PrescriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prescription
        fields = '__all__'

class MedicalRecordListSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalRecord
        fields = ['record_id', 'appointment', 'diagnosis', 'treatment', 'result', 'record_note']

class MedicalRecordDetailSerializer(serializers.ModelSerializer):

    patient_tests = PatientTestSerializer(many=True, read_only=True)
    prescriptions = PrescriptionSerializer(many=True, read_only=True)

    class Meta:
        model = MedicalRecord
        fields = [
            'record_id', 'appointment', 'diagnosis', 'treatment', 'result', 'record_note',
            'patient_tests', 'prescriptions'
        ]


class PaymentDetailSerializer(serializers.Serializer):
    class Meta:
        model = PaymentDetail
        fields = ['detail_id', 'service_type', 'service_id', 'service_name',
                   'amount', 'detail_status']

class PaymentSerializer(serializers.ModelSerializer):
    details = PaymentDetailSerializer(many=True, read_only=True)
    class Meta:
        model = Payment
        fields = [
            'payment_id', 'appointment', 'total_amount', 'payment_status',
            'payment_type', 'order_code', 'payment_method', 'payment_timestamp', 'details'
        ]