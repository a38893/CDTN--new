import random
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from datetime import date, time



class UserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError('Tên đăng nhập là bắt buộc.')
        user = self.model(username=username, **extra_fields)
        user.set_password(password)  # Mã hóa mật khẩu
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('role', 'admin')
        extra_fields.setdefault('status', 'active')
        return self.create_user(username, password, **extra_fields)

class OtpUsers(models.Model):
    otp_id = models.AutoField(primary_key=True)
    user= models.ForeignKey('User', on_delete=models.CASCADE, related_name='otp_users')
    is_verified  = models.BooleanField(default=False)
    otp_code = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'otp_users'
class User(AbstractBaseUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('receptionist', 'Lễ tân'),
        ('doctor', 'Bác sĩ'),
        ('patient', 'Bệnh nhân'),
    ]
    user_id = models.AutoField(primary_key=True, verbose_name='Mã người dùng')
    username = models.CharField(max_length=50, unique=True, verbose_name='Tên đăng nhập')
    password = models.CharField(max_length=128, verbose_name='Mật khẩu')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='patient', verbose_name='Vai trò')
    status = models.BooleanField( default=False, verbose_name='Trạng thái hoạt động') 
    full_name = models.CharField(max_length=100, verbose_name='Họ và tên')
    gender = models.CharField(max_length=10,choices =[("Nam", "Nam"), ("Nữ", "Nữ"), ("Khác", "Khác")],default= "Nam", verbose_name='Giới tính')
    address = models.TextField(verbose_name='Địa chỉ')
    birth_day = models.DateField(verbose_name='Ngày sinh', blank=True, null=True) 
    phone = models.CharField(max_length=10, unique= True, verbose_name='Số điện thoại')
    gmail = models.EmailField(max_length=100,unique=True, verbose_name='Email')     
    specialty = models.CharField(max_length=50, blank=True, null=True, verbose_name='Chuyên khoa')
    degree = models.CharField(max_length=50, blank=True, null=True, verbose_name='Bằng cấp')
    img = models.ImageField(upload_to='img/', blank=True, null=True, verbose_name='Ảnh đại diện')
    objects = UserManager()
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['full_name', 'gender', 'address', 'birth_day', 'phone']


    def __str__(self):
        return self.username

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return self.role in ['admin', 'receptionist', 'doctor']

    @property
    def is_superuser(self):
        return self.role == 'admin'

    @property
    def is_staff(self):
        return self.role in ['admin', 'receptionist', 'doctor']

    @property
    def is_active(self):
        return self.status

    class Meta:
        db_table = 'users'
        verbose_name = 'Người dùng'    
        verbose_name_plural = 'Người dùng'

class Appointment(models.Model):
    appointment_id = models.AutoField(primary_key=True, verbose_name='Mã lịch hẹn')
    patient_user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments_as_patient', verbose_name='Người dùng bệnh nhân')
    doctor_user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments_as_doctor', verbose_name='Người dùng bác sĩ')
    appointment_day = models.DateField(default=date.today, verbose_name='Ngày hẹn')
    appointment_status = models.CharField(max_length=20, default='pending', verbose_name='Trạng thái lịch hẹn', choices=[
        ('pending', 'Đang chờ'),
        ('confirmed', 'Đã xác nhận'),
        ('cancelled', 'Đã hủy'),
        ('completed', 'Đã hoàn thành')])
    appointment_time = models.TimeField(default=time(12, 0), verbose_name='Giờ hẹn')
    appointment_created_at = models.DateTimeField(auto_now_add=True, verbose_name='Ngày tạo lịch hẹn')
    appointment_updated_at = models.DateTimeField(auto_now=True, verbose_name='Ngày cập nhật lịch hẹn')

    def __str__(self):
        return f"{self.appointment_id} - {self.patient_user_id.full_name} - {self.doctor_user_id.full_name} - {self.appointment_day} {self.appointment_time}"

    class Meta:
        db_table = 'appointments'
        ordering = ['-appointment_day', '-appointment_time']  
        verbose_name = 'Lịch hẹn'    
        verbose_name_plural = 'Lịch hẹn'
class MedicalRecord(models.Model):
    RECORD_STATUS_CHOICES = [
        ('done', 'đã xong'),
        ('loading', 'đang tiến hành'),
        
    ]
    record_id = models.AutoField(primary_key=True, verbose_name='Mã hồ sơ bệnh án')
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='medical_records', verbose_name='Lịch hẹn')
    record_status = models.CharField( choices=RECORD_STATUS_CHOICES,max_length=20, default='loading', verbose_name='Trạng thái hồ sơ bệnh án')
    record_note = models.TextField(blank=True, null=True, verbose_name='Ghi chú')
    diagnosis = models.TextField(blank=True, null=True, verbose_name='Chẩn đoán')
    treatment = models.TextField(blank=True, null=True, verbose_name='Điều trị')
    record_result = models.TextField(blank=True, null=True, verbose_name='Kết quả')

    def __str__(self):
        return f"Medical Record {self.record_id}"

    class Meta:
        db_table = 'medical_records'
        verbose_name = 'Hồ sơ bệnh án'    
        verbose_name_plural = 'Hồ sơ bệnh án'

class PatientTest(models.Model):
    STATUS_CHOICES = [('Pending', 'Đang chờ thanh toán'),
        ('Done', 'Đã xong'),
        ('Waiting', 'Đang chờ kết quả'),
        ('Cancelled', 'Đã hủy'),
        ('In Progress', 'Đang tiến hành'),
        ]
    patient_test_id = models.AutoField(primary_key=True, verbose_name='Mã xét nghiệm bệnh nhân')
    record = models.ForeignKey(MedicalRecord, on_delete=models.CASCADE, related_name='patient_tests', verbose_name='Hồ sơ bệnh án')
    test = models.ForeignKey('LabTest', on_delete=models.CASCADE, related_name='patient_tests', verbose_name='Xét nghiệm')
    test_result = models.TextField(blank=True, null=True, verbose_name='Kết quả xét nghiệm')
    test_date = models.DateField(verbose_name='Ngày xét nghiệm')
    test_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending', verbose_name='Trạng thái xét nghiệm')
    performed_by_doctor = models.ForeignKey(User, on_delete=models.CASCADE,null = True, blank= True, related_name='performed_tests', verbose_name='Bác sĩ thực hiện xét nghiệm')

    def __str__(self):
        return f"Patient Test {self.patient_test_id}"

    class Meta:
        db_table = 'patient_tests'
        verbose_name = 'Xét nghiệm bệnh nhân'    
        verbose_name_plural = 'Xét nghiệm bệnh nhân'

class LabTest(models.Model):
    test_id = models.AutoField(primary_key=True, verbose_name='Mã xét nghiệm')
    test_name = models.CharField(max_length=100, verbose_name='Tên xét nghiệm')
    test_description = models.TextField(verbose_name='Mô tả xét nghiệm')
    test_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Giá xét nghiệm')
    test_category = models.CharField(max_length=100, verbose_name='Loại xét nghiệm')

    def __str__(self):
        return self.test_name

    class Meta:
        db_table = 'lab_test'
        verbose_name = 'Xét nghiệm'    
        verbose_name_plural = 'Xét nghiệm'


class Medication(models.Model):
    medication_id = models.AutoField(primary_key=True, verbose_name='Mã thuốc')
    medication_name = models.CharField(max_length=100, verbose_name='Tên thuốc')
    medication_description = models.TextField(verbose_name='Mô tả thuốc')
    medication_unit = models.CharField(max_length=20, verbose_name='Đơn vị thuốc')
    medication_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Giá thuốc')
    recommended_dosage = models.CharField(max_length=50, verbose_name='Liều lượng khuyến nghị')
    expiration_date = models.DateField(verbose_name='Ngày hết hạn')
    stock_quantity = models.IntegerField(verbose_name='Số lượng tồn kho')
    medication_category = models.CharField(max_length=100, verbose_name='Loại thuốc')

    def __str__(self):
        return self.medication_name

    class Meta:
        db_table = 'medications'
        verbose_name = 'Thuốc'    
        verbose_name_plural = 'Thuốc'

class Prescription(models.Model):
    prescription_id = models.AutoField(primary_key=True, verbose_name='Mã đơn thuốc') 
    record = models.ForeignKey(MedicalRecord, on_delete=models.CASCADE, related_name='prescriptions',   verbose_name='Hồ sơ bệnh án')
    medication = models.ForeignKey(Medication, on_delete=models.CASCADE, related_name='prescriptions', verbose_name='Thuốc')
    duration = models.CharField(max_length=128, verbose_name='Thời gian sử dụng')  
    dosage = models.CharField(max_length=50, verbose_name='Liều lượng sử dụng')
    prescription_quantity = models.IntegerField(verbose_name='Số lượng thuốc')
    instructions = models.TextField(verbose_name='Hướng dẫn sử dụng')
    frequency = models.CharField(max_length=50, verbose_name='Tần suất sử dụng')

    def __str__(self):
        return f"Prescription {self.prescription_id}"

    class Meta:
        db_table = 'prescription'
        verbose_name = 'Đơn thuốc'    
        verbose_name_plural = 'Đơn thuốc'
        
class Payment(models.Model):
    payment_id = models.AutoField(primary_key=True, verbose_name='Mã hóa đơn thanh toán')
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='payments', verbose_name='Lịch hẹn')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Tổng số tiền')
    payment_status = models.CharField(
        max_length=20,verbose_name='Trạng thái thanh toán',
        choices=[('unpaid', 'Chưa thanh toán'), ('paid', 'Đã thanh toán')],
        default='unpaid'
    )
    payment_type = models.CharField(max_length=20, choices=[('test', 'Xét nghiệm'), ('prescription', 'thuốc'), ('deposit', 'Đặt cọc')], default='deposit', blank=True, null=True, verbose_name='Loại thanh toán')
    order_code = models.CharField(max_length=20, unique=True, verbose_name='Mã đơn hàng') 
    payment_method = models.CharField(choices=[('banking', 'Chuyển khoản'),('cash', 'Tiền mặt')] ,max_length=50, blank=True, null=True, verbose_name='Phương thức thanh toán')
    payment_timestamp = models.DateTimeField(auto_now_add=True, verbose_name='Thời gian thanh toán')
    vnp_create_date = models.CharField(max_length=14, blank=True, null=True, verbose_name='Ngày tạo VNPAY')  

    def save(self, *args, **kwargs):
        is_new_paid = False
        if self.pk:
            old = Payment.objects.get(pk=self.pk)
            if old.payment_status != 'paid' and self.payment_status == 'paid':
                is_new_paid = True
        else:
            if self.payment_status == 'paid':
                is_new_paid = True

        if not self.order_code:
            while True:
                code = f"ORD{random.randint(100000, 999999)}"
                if not Payment.objects.filter(order_code=code).exists():
                    self.order_code = code
                    break
        super().save(*args, **kwargs)
        if is_new_paid:
            self.details.update(detail_status='paid', detail_method=self.payment_method)
            # Nếu là chuyển khoản và chưa có phương thức thì gán banking
            if not self.payment_method:
                self.payment_method = 'banking'
                super().save(update_fields=['payment_method'])
        if self.payment_type == 'test' and is_new_paid: 
            medical_record = getattr(self.appointment, 'medical_records', None)
            if medical_record:
                medical_record.patient_tests.filter(test_status='Pending').update(test_status='In Progress')
    def __str__(self):
        return f"Hóa đơn #{self.payment_id} - {self.get_payment_status_display()}"

    class Meta:
        db_table = 'payments'
        verbose_name = 'Hóa đơn thanh toán'    
        verbose_name_plural = 'Hóa đơn thanh toán'


class PaymentDetail(models.Model):
    detail_id = models.AutoField(primary_key=True, verbose_name='Mã chi tiết thanh toán')
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='details', verbose_name='Hóa đơn thanh toán')
    service_type = models.CharField(max_length=50, verbose_name= 'Loại dịch vụ')  
    service_id = models.IntegerField(verbose_name='Mã dịch vụ')             
    service_name = models.CharField(max_length=255, verbose_name='Tên dịch vụ') 
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Số tiền')
    detail_quantity = models.PositiveIntegerField(default=1, verbose_name='Số lượng dịch vụ')
    detail_status = models.CharField(
        max_length=20, verbose_name='Trạng thái chi tiết thanh toán',
        choices=[('unpaid', 'Chưa thanh toán'), ('paid', 'Đã thanh toán')],
        default='unpaid'
    ) 
    detail_method = models.CharField(max_length=50, blank=True, null=True, verbose_name='Phương thức thanh toán')
    def __str__(self):
        return f"{self.service_name} ({self.amount})"

    class Meta:
        db_table = 'payment_details'
        verbose_name = 'Chi tiết thanh toán'    
        verbose_name_plural = 'Chi tiết thanh toán'