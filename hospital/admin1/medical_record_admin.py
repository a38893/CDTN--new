from django import forms
from django.contrib import admin
from hospital.models import MedicalRecord, PatientTest, Prescription, Appointment, PaymentDetail, Payment, Medication, PrescriptionDetail
from django.utils import timezone
from django.db import models
from django.core.exceptions import ValidationError
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from django.forms.models import BaseInlineFormSet
from django.contrib.auth import get_user_model
from django.contrib.admin import SimpleListFilter
# from hospital.admin1.PatientTestInlineForm import PatientTestInline
class MedicalRecordResource(resources.ModelResource):
    class Meta:
        model = MedicalRecord





class PatientTestInline(admin.TabularInline):
    model = PatientTest
    extra = 1
    exclude = ('test_status', 'test_date')
    autocomplete_fields = ('test',)

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        if request.user.role == 'doctor':
            return readonly + ['test_result', 'performed_by_doctor']
        return readonly

    def save_new_instance(self, form, commit=True):
        obj = super().save_new_instance(form, commit=False)
        request = form.request if hasattr(form, 'request') else None
        if request and obj.test_result and obj.performed_by_doctor is None:
            obj.performed_by_doctor = request.user
        if commit:
            obj.save()
        return obj

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for obj in instances:
            if obj.test_result and obj.performed_by_doctor is None:
                obj.performed_by_doctor = request.user
            obj.save()
        formset.save_m2m()
class PrescriptionInline(admin.TabularInline):
    model = Prescription
    extra = 1
    fields = ( 'prescription_status','instructions' )
    show_change_link = True
    readonly_fields = ('prescription_status',)


class MedicalReocrdForm(forms.ModelForm):
    class Meta:
        model = MedicalRecord
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        appointment = cleaned_data.get('appointment')    
        if appointment and appointment.appointment_status != 'full':
            raise ValidationError("Chưa thanh toán tiền khám!")
        return cleaned_data

@admin.register(MedicalRecord)
class MedicalRecordAdmin(ImportExportModelAdmin):
    resource_class = MedicalRecordResource
    list_display = ('record_id_display', 'appointment_display','get_patient_id', 'record_status_display', 'diagnosis_display', 'treatment_display', 'record_result_display')
    search_fields = ('record_id', 'appointment__appointment_id','appointment__patient_user_id__exact')
    inlines = [PatientTestInline, PrescriptionInline]
    autocomplete_fields = ('appointment',)
    raw_id_fields = ('appointment',)
    form = MedicalReocrdForm

    def get_patient_id(self, obj):
        # Kiểm tra liên kết appointment và patient_user_id có tồn tại không
        if obj.appointment and obj.appointment.patient_user_id:
            return obj.appointment.patient_user_id.pk  
        return ''
    get_patient_id.short_description = 'Mã bệnh nhân'

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

    def save_model(self, request, obj, form, change):
        is_new = obj.pk is None
        super().save_model(request, obj, form, change)
        if is_new:
            Prescription.objects.create(
                record=obj,
                prescription_status='unpaid',
                instructions=''
            )


    def save_formset(self, request, form, formset, change):
        if not formset.is_valid():
            return 

        instances = formset.save(commit=False)
        new_tests = []
        appointment = None

        # Xác định các PatientTest mới được thêm (chưa có trong DB)
        for obj in instances:
            is_new = obj.pk is None
            obj.save()
            if isinstance(obj, PatientTest) and is_new:
                new_tests.append(obj)
                appointment = obj.record.appointment

        formset.save_m2m()

        # Nếu có xét nghiệm mới được thêm, tạo Payment và PaymentDetail mới
        if new_tests and appointment:
            total_amount = sum(getattr(test.test, 'test_price', 0) for test in new_tests)
            payment = Payment.objects.create(
                appointment=appointment,
                payment_type='test',
                total_amount=total_amount,
                payment_status='unpaid',
                payment_method='',
                payment_timestamp=timezone.now()
            )
            for test in new_tests:
                PaymentDetail.objects.create(
                    payment=payment,
                    service_type='test',
                    service_id=test.test.test_id,
                    service_name=str(test.test),
                    amount=getattr(test.test, 'test_price', 0),
                    detail_quantity=1,
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
    
