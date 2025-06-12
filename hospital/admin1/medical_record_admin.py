from django import forms
from django.contrib import admin
from hospital.models import MedicalRecord, PatientTest, Prescription, Appointment, PaymentDetail, Payment
from django.utils import timezone
from django.db import models







class PatientTestInline(admin.TabularInline):
    model = PatientTest
    extra = 1
    exclude = ('test_status','test_date')  
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
        details_by_type = {'test': [], 'prescription': []}
        appointment = None

        for obj in instances:
            obj.save()
            appointment = obj.record.appointment

            if isinstance(obj, PatientTest):
                service_type = 'test'
                service_id = obj.test.test_id
                service_name = str(obj.test)
                amount = getattr(obj.test, 'test_price', 0)
                if PaymentDetail.objects.filter(service_type=service_type, service_id=service_id, detail_status='unpaid', payment__appointment=appointment).exists():
                    continue
                details_by_type['test'].append({
                    'service_type': service_type,
                    'service_id': service_id,
                    'service_name': service_name,
                    'amount': amount,
                    'detail_quantity': 1
                })
            elif isinstance(obj, Prescription):
                service_type = 'prescription'
                service_id = obj.medication.medication_id
                service_name = f"Thuốc: {obj.medication.medication_name}"
                amount = getattr(obj.medication, 'medication_price', 0)
                quantity = getattr(obj, 'prescription_quantity', 1)
                if PaymentDetail.objects.filter(service_type=service_type, service_id=service_id, detail_status='unpaid', payment__appointment=appointment).exists():
                    continue
                details_by_type['prescription'].append({
                    'service_type': service_type,
                    'service_id': service_id,
                    'service_name': service_name,
                    'amount': amount,
                    'detail_quantity': quantity
                })
        formset.save_m2m()

    # Tạo Payment và PaymentDetail cho từng loại dịch vụ nếu có dịch vụ mới
        for payment_type, details in details_by_type.items():
            if details and appointment:
                total_amount = sum(d['amount'] * d.get('detail_quantity', 1) for d in details)
                payment = Payment.objects.create(
                    appointment=appointment,
                    payment_type=payment_type,
                    total_amount=total_amount,
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
                        detail_quantity=d.get('detail_quantity', 1),
                        detail_status='unpaid'
                    )

        # Cập nhật lại tổng tiền cho các payment đã tồn tại (nếu cần)
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
                total = payment.details.aggregate(
                    total=models.Sum(models.F('amount') * models.F('detail_quantity'))
                )['total'] or 0
                payment.total_amount = total
                payment.save()
            for d in details:
                PaymentDetail.objects.create(
                    payment=payment,
                    service_type=d['service_type'],
                    service_id=d['service_id'],
                    service_name=d['service_name'],
                    amount=d['amount'],
                    detail_quantity=d.get('detail_quantity', 1), 
                    detail_status='unpaid'
    )

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
