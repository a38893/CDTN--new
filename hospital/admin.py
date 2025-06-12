from django.utils import timezone
from django.db import models
from django.contrib import admin
from .models import Appointment, AbstractBaseUser, UserManager, LabTest, Medication, MedicalRecord, Payment, PatientTest,PaymentDetail, User, Prescription
from django import forms
from django.contrib.auth.hashers import make_password

# # Register your models here.
# admin.site.register(Appointment)
# admin.site.register(PrescriptionDetail)
# admin.site.register(LabTest)
# admin.site.register(Medication)
# admin.site.register(MedicalRecord)
# admin.site.register(Payment)
# admin.site.register(PatientTest)
# admin.site.register(User)
admin.site.register(Prescription)
# admin.site.register(PaymentDetail)
admin.site.site_header = "Quản lý phòng khám LHM"



@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('appointment_id', 'patient_user_id', 'doctor_user_id', 'appointment_day', 'appointment_time', 'appointment_status')
    search_fields = ('patient_user_id__username', 'doctor_user_id__username', 'appointment_day', 'appointment_time', 'appointment_id')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.role in ['admin', 'receptionist']:
            return qs
        elif request.user.role == 'doctor':
            return qs.filter(doctor_user_id=request.user)
        return qs.none()
    
    def has_view_permission(self, request, obj = None):
        return request.user.role in ['admin', 'receptionist', 'doctor']

    def has_change_permission(self, request, obj=None):
        return request.user.role in ['admin', 'receptionist']
    
    def has_delete_permission(self, request, obj=None):
        return request.user.role in ['admin', 'receptionist']
    def has_add_permission(self, request):
        return request.user.role in ['admin', 'receptionist']

class UserAdminForm(forms.ModelForm):
    class Meta:
        model = User
        fields = '__all__'

    def clean_role(self):
        role = self.cleaned_data.get('role')
        user = self.current_user

        if user.role == 'receptionist' and role != 'patient':
            raise forms.ValidationError("Lễ tân chỉ tạo được tài khoản với vai trò lễ tân!")
        return role
    
    def __init__(self, *args, **kwargs):
        self.current_user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)
        if self.current_user and self.current_user.role == 'receptionist':
            self.fields['role'].choices = [('patient', 'Patient')]

class UsersAdmin(admin.ModelAdmin):
    form = UserAdminForm
    list_display = ('user_id', 'username', 'role', 'full_name', 'phone','gmail')
    search_fields= ('username','full_name', 'phone', 'gmail','user_id')
    list_filter = ('role',)
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        class CustomForm(form):
            def __new__(cls, *args, **kwargs2):
                kwargs2['current_user'] = request.user
                return form(*args, **kwargs2)
        return CustomForm
    def save_model(self, request, obj, form, change):
        # Nếu mật khẩu vừa nhập khác với mật khẩu đã hash (hoặc là mật khẩu mới)
        raw_password = form.cleaned_data.get('password')
        if raw_password and not raw_password.startswith('pbkdf2_'):
            obj.password = make_password(raw_password)
        super().save_model(request, obj, form, change)
    

    def has_view_permission(self, request, obj=None):
        return request.user.role in ['admin', 'receptionist']

    def has_change_permission(self, request, obj=None):
        return request.user.role == 'admin'

    def has_delete_permission(self, request, obj=None):
        return request.user.role == 'admin'

    def has_add_permission(self, request):
        return request.user.role in ['admin', 'receptionist']
    
admin.site.register(User, UsersAdmin)


class PatientTestInline(admin.TabularInline):
    model = PatientTest
    extra = 1
    exclude = ('test_status',)  
    autocomplete_fields = ('test',)
    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        return [f for f in fields if f != 'test_status']

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        if request.user.role == 'doctor':
            return readonly + ['test_result', 'performed_by_doctor']
        return readonly
    def save_new_instance(self, form, commit=True):
        obj = super().save_new_instance(form, commit=False)
        request = form.request if hasattr(form, 'request') else None
        # Nếu đã nhập test_result và performed_by_doctor đang null thì gán user đang đăng nhập
        if request and obj.test_result and obj.performed_by_doctor is None:
            obj.performed_by_doctor = request.user
        if commit:
            obj.save()
        return obj

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for obj in instances:
            # Nếu đã nhập test_result và performed_by_doctor đang null thì gán user đang đăng nhập
            if obj.test_result and obj.performed_by_doctor is None:
                obj.performed_by_doctor = request.user
            obj.save()
        formset.save_m2m()

class PrescriptionInline(admin.TabularInline):
    model = Prescription
    extra = 1
    autocomplete_fields = ('medication',)
class MedicalRecordForm(forms.ModelForm):
    class Meta:
        model = MedicalRecord
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Chỉ set queryset nếu trường 'appointment' có trong form
        if 'appointment' in self.fields:
            qs = Appointment.objects.filter(appointment_status='confirmed').exclude(medical_records__isnull=False)
            if self.instance and self.instance.pk and hasattr(self.instance, 'appointment_id'):
                # Khi sửa, cho phép chọn lại appointment cũ
                qs = qs | Appointment.objects.filter(pk=self.instance.appointment_id)
            self.fields['appointment'].queryset = qs
@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    form = MedicalRecordForm
    list_display = ('record_id_display', 'appointment_display', 'record_status_display', 'diagnosis_display', 'treatment_display', 'record_result_display')
    search_fields = ('record_id', 'appointment__appointment_id', 'diagnosis')
    inlines = [PatientTestInline, PrescriptionInline]
    autocomplete_fields = ('appointment',)

    def record_status_display(self, obj):
        return obj.get_record_status_display()
    record_status_display.short_description = 'Trạng thái'
    def diagnosis_display(self, obj):
        return obj.diagnosis
    diagnosis_display.short_description = 'Chẩn đoán'
    def treatment_display(self, obj):
        return obj.treatment
    treatment_display.short_description = 'Điều trị'
    def record_result_display(self, obj):
        return obj.record_result
    record_result_display.short_description = 'Kết quả'
    def appointment_display(self, obj):
        return obj.appointment
    appointment_display.short_description = 'Lịch hẹn'
    def record_id_display(self, obj):
        return obj.record_id
    record_id_display.short_description = 'Mã hồ sơ'
    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        # Gom các dịch vụ mới theo loại
        details_by_type = {'test': [], 'prescription': []}
        appointment = None

        for obj in instances:
            obj.save()
            obj.refresh_from_db()
            appointment = obj.record.appointment

            if isinstance(obj, PatientTest):
                payment_type = 'test'
                amount = getattr(obj.test, 'test_price', 0)
                service_type = 'test'
                service_id = obj.test.test_id  # Lưu test_id
                service_name = str(obj.test)
                if PaymentDetail.objects.filter(service_type=service_type, service_id=service_id, detail_status='paid').exists():
                    continue
                details_by_type['test'].append({
                    'service_type': service_type,
                    'service_id': service_id,
                    'service_name': service_name,
                    'amount': amount
                })
            elif isinstance(obj, Prescription):
                payment_type = 'prescription'
                amount = getattr(obj.medication, 'medication_price', 0) * getattr(obj, 'quantity', 1)
                service_type = 'prescription'
                service_id = obj.medication.medication_id  # Lưu medication_id
                service_name = f"Thuốc: {obj.medication.medication_name}"
                if PaymentDetail.objects.filter(service_type=service_type, service_id=service_id, detail_status='paid').exists():
                    continue
                details_by_type['prescription'].append({
                    'service_type': service_type,
                    'service_id': service_id,
                    'service_name': service_name,
                    'amount': amount
                })
        formset.save_m2m()

        # Tạo mới Payment và PaymentDetail cho từng loại dịch vụ nếu có dịch vụ mới chưa thanh toán
        for payment_type, details in details_by_type.items():
            if details and appointment:
                payment = Payment.objects.create(
                    appointment=appointment,
                    payment_type=payment_type,
                    total_amount=sum(d['amount'] for d in details),
                    payment_status='unpaid',
                    payment_method='',
                    payment_timestamp=timezone.now()
                )
                for d in details:
                    PaymentDetail.objects.create(
                        payment=payment,
                        service_type=d['service_type'],
                        service_id=d['service_id'],
                        service_name=d['service_name'],
                        amount=d['amount'],
                        detail_status='unpaid')


            formset.save_m2m()
            if instances:
                payment_types = set()
                for obj in instances:
                    if isinstance(obj, PatientTest):
                        payment_types.add('test')
                    elif isinstance(obj, Prescription):
                        payment_types.add('prescription')
                for payment_type in payment_types:
                    payment = Payment.objects.filter(
                        appointment=instances[0].record.appointment,
                        payment_type=payment_type
                    ).first()
                    if payment:
                        total = payment.details.aggregate(total=models.Sum('amount'))['total'] or 0
                        payment.total_amount = total
                        payment.save()

    def has_view_permission(self, request, obj=None):
        # Admin và lễ tân đều xem được, bác sĩ cũng xem được nếu là bác sĩ của record
        return request.user.role in ['admin', 'receptionist', 'doctor']


    def has_change_permission(self, request, obj=None):
        if request.user.role == 'admin':
            return True
        if request.user.role == 'doctor':
            if obj is None:
                return True
            return obj.appointment.doctor_user_id == request.user
        if request.user.role == 'receptionist':
            if obj and obj.record_status == 'đang tiến hành':
                return True
        return False

    def has_add_permission(self, request):
        # Admin và bác sĩ được thêm
        return request.user.role in ['admin', 'doctor']

    def has_delete_permission(self, request, obj=None):
        # Chỉ admin được xóa
        return request.user.role == 'admin'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.role in ['admin', 'receptionist']:
            return qs
        elif request.user.role == 'doctor':
            return qs.filter(appointment__doctor_user_id=request.user)
        
        return qs.none()

@admin.register(Medication)
class MedicationAdmin(admin.ModelAdmin):
    list_display = ('medication_id', 'medication_name', 'medication_unit', 'medication_price', 'stock_quantity')
    search_fields = ('medication_name', 'medication_category')

    def has_view_permission(self, request, obj=None):
        # Admin, lễ tân, bác sĩ đều xem được
        return request.user.role in ['admin', 'receptionist', 'doctor']

    def has_change_permission(self, request, obj=None):
        # Admin và lễ tân được sửa
        return request.user.role in ['admin', 'receptionist']

    def has_add_permission(self, request):
        # Admin và lễ tân được thêm
        return request.user.role in ['admin', 'receptionist']

    def has_delete_permission(self, request, obj=None):
        # Admin và lễ tân được xóa
        return request.user.role in ['admin', 'receptionist']
    
@admin.register(LabTest)
class LabTestAdmin(admin.ModelAdmin):
    list_display = ('test_id', 'test_name', 'test_category', 'test_price')
    search_fields = ('test_name', 'test_category')

    def has_view_permission(self, request, obj=None):
        # Admin, lễ tân, bác sĩ đều xem được
        return request.user.role in ['admin', 'receptionist', 'doctor']

    def has_change_permission(self, request, obj=None):
        # Admin và lễ tân được sửa
        return request.user.role in ['admin', 'receptionist']

    def has_add_permission(self, request):
        # Admin và lễ tân được thêm
        return request.user.role in ['admin', 'receptionist']

    def has_delete_permission(self, request, obj=None):
        # Admin và lễ tân được xóa
        return request.user.role in ['admin', 'receptionist']
    
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('payment_id', 'appointment', 'total_amount', 'payment_status', 'payment_method', 'payment_timestamp')
    search_fields = ('appointment__appointment_id', 'payment_status', 'payment_method')
    list_filter = ('payment_status', 'payment_method')
    def has_view_permission(self, request, obj=None):
        # Admin, lễ tân, bác sĩ đều xem được
        return request.user.role in ['admin', 'receptionist']

    def has_change_permission(self, request, obj=None):
        # Admin và lễ tân được sửa
        return request.user.role in ['admin', 'receptionist']

    def has_add_permission(self, request):
        # Admin và lễ tân được thêm
        return request.user.role in ['admin', 'receptionist']

    def has_delete_permission(self, request, obj=None):
        # Admin và lễ tân được xóa
        return request.user.role in ['admin']
    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        # Nếu đã paid thì tất cả các trường đều readonly
        if obj and obj.payment_status == 'paid':
            # Lấy tất cả các trường trừ id
            all_fields = [f.name for f in self.model._meta.fields if f.name != 'payment_id']
            return readonly + all_fields
        return readonly

    def has_delete_permission(self, request, obj=None):
        # Không cho phép xóa nếu đã paid
        if obj and obj.payment_status == 'paid':
            return False
        return super().has_delete_permission(request, obj)
@admin.register(PaymentDetail)
class PaymentDetailAdmin(admin.ModelAdmin):
    # Hiện tất cả các trường của model
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.fields]

    search_fields = ('payment__appointment__appointment_id', 'service_type', 'service_name')
    list_filter = ('service_type',)

    def has_view_permission(self, request, obj=None):
        # Lễ tân và admin đều xem được
        return request.user.role in ['admin', 'receptionist']

    def has_change_permission(self, request, obj=None):
        # Chỉ admin được sửa
        return request.user.role == 'admin'

    def has_add_permission(self, request):
        # Chỉ admin được thêm
        return request.user.role == 'admin'

    def has_delete_permission(self, request, obj=None):
        # Chỉ admin được xóa
        return request.user.role == 'admin'

    def get_readonly_fields(self, request, obj=None):
        # Lễ tân luôn readonly tất cả trường
        if request.user.role == 'receptionist':
            return [field.name for field in self.model._meta.fields]
        return super().get_readonly_fields(request, obj)
@admin.register(PatientTest)
class PatientTestAdmin(admin.ModelAdmin):
    list_display = ('patient_test_id', 'record','test_result', 'test', 'test_date', 'test_status', 'performed_by_doctor')
    search_fields = ('record__appointment__appointment_id', 'test__test_name', 'performed_by_doctor__username')
    list_filter = ('test_status', 'test__test_category')
    def has_view_permission(self, request, obj=None):
        # Admin, lễ tân, bác sĩ đều xem được
        return request.user.role in ['admin', 'receptionist', 'doctor']

    def has_change_permission(self, request, obj=None):
        # Admin và lễ tân được sửa
        return request.user.role in ['admin', 'receptionist', 'doctor']

    def has_add_permission(self, request):
        # Admin và lễ tân được thêm
        return request.user.role in ['admin', 'receptionist', 'doctor']

    def has_delete_permission(self, request, obj=None):
        # Admin và lễ tân được xóa
        return request.user.role in ['admin', 'receptionist', 'doctor']