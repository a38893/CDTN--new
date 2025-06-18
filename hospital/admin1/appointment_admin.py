
from django.db import models
from django.contrib import admin
from hospital.models import Appointment, User, Payment, PaymentDetail, DegreeExamFee
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from django import forms
from django.contrib.auth import get_user_model

from hospital.api.gen_time_slots import generate_time_slots
class AppointmentResource(resources.ModelResource):
    class Meta:
        model = Appointment

class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = '__all__'
    # lấy khung giờ cho phép đặt lịch
def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    time_choice = [(t, t) for t in generate_time_slots()]
    if 'appointment_time' in self.fields:
        self.fields['appointment_time'].widget = forms.Select(choices=time_choice)
        if not self.instance or not self.instance.pk:
            # Nếu tạo mới thì mặc định là 08:00
            self.fields['appointment_time'].initial = '08:30'
    # def clean(self):
    #     cleaned_data = super().clean()
    #     doctor = cleaned_data.get('doctor_user_id')
    #     day = cleaned_data.get('appointment_day')
    #     time = cleaned_data.get('appointment_time')
    #     status_list = ['pending', 'confirmed', 'full']
    #     if doctor and day and time:
    #         qs = Appointment.objects.filter(
    #             doctor_user_id=doctor,
    #             appointment_day=day,
    #             appointment_time=time,
    #             appointment_status__in=status_list
    #         )
    #         if self.instance.pk:
    #             qs = qs.exclude(pk=self.instance.pk)
    #         if qs.exists():
    #             raise forms.ValidationError("Bác sĩ đã có lịch hẹn vào thời gian này. Vui lòng chọn thời gian khác!")
    #     return cleaned_data


@admin.register(Appointment)
class AppointmentAdmin(ImportExportModelAdmin):
    resource_class = AppointmentResource
    form = AppointmentForm
    autocomplete_fields = ('patient_user_id', 'doctor_user_id')
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
    


    def save_model(self, request, obj, form, change):
        is_new = obj.pk is None
        if not is_new:
            old_obj = Appointment.objects.get(pk=obj.pk)
            old_status = old_obj.appointment_status
        else:
            old_status = None

        super().save_model(request, obj, form, change)



        degree = obj.doctor_user_id.doctor_profile.degree
        exam_fee = degree.fee if degree else 0
        deposit = 30000
        full = exam_fee - deposit
        if full < 0:
                full = 0
        if old_status =='pending' and obj.appointment_status == 'confirmed':
            if not Payment.objects.filter(appointment=obj, payment_type='exam').exists():
                    payment = Payment.objects.create(
                        appointment=obj,
                        payment_type='exam',
                        total_amount=full,
                        payment_status='unpaid',
                        payment_method='',
                    )
                    PaymentDetail.objects.create(
                        payment=payment,
                        service_type='exam',
                        service_id=-1,
                        service_name='Phí khám bệnh còn lại',
                        amount=full,
                        detail_quantity=1,
                        detail_status='unpaid',
                    )

        if is_new and obj.appointment_status == 'confirmed':
            if not Payment.objects.filter(appointment=obj, payment_type='exam').exists():
                payment = Payment.objects.create(
                    appointment=obj,
                    payment_type='exam',
                    total_amount=exam_fee,
                    payment_status='unpaid',
                    payment_method='',
                )
                PaymentDetail.objects.create(
                    payment=payment,
                    service_type='exam',
                    service_id=-1,
                    service_name='Phí khám bệnh',
                    amount=exam_fee,
                    detail_quantity=1,
                    detail_status='unpaid',)

            