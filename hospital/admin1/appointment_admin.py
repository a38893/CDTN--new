
from django.db import models
from django.contrib import admin
from hospital.models import Appointment, User, Payment, PaymentDetail
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from django import forms
from hospital.degree_exam_fee import degree_exam_fee
class AppointmentResource(resources.ModelResource):
    class Meta:
        model = Appointment






@admin.register(Appointment)
class AppointmentAdmin(ImportExportModelAdmin):
    resource_class = AppointmentResource
    list_display = ('appointment_id', 'patient_user_id', 'doctor_user_id', 'appointment_day', 'appointment_time', 'appointment_status')
    search_fields = ('patient_user_id__username', 'doctor_user_id__username', 'appointment_day', 'appointment_time', 'appointment_id')
    autocomplete_fields = ('patient_user_id', 'doctor_user_id')
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
    # lọc appointment_id trạng thái đã thanh toán tiền khám
    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        queryset = queryset.filter(appointment_status='full')
        return queryset, use_distinct

    def save_model(self, request, obj, form, change):
        if obj.pk:
            old_obj = Appointment.objects.get(pk=obj.pk)
            old_status = old_obj.appointment_status
        else:
            old_status = None
        super().save_model(request, obj, form, change)

        if old_status == 'pending' and obj.appointment_status in ['full', 'confirmed']:
            degree = obj.doctor_user_id.doctor_profile.degree
            exam_fee = degree_exam_fee.get(degree, 0)
            deposit = 30000
            total_after_discount = int(exam_fee * 0.85)
            full = total_after_discount - deposit
            if full < 0:
                full = 0


            if not Payment.objects.filter(appointment=obj, payment_type='exam').exists():
                if obj.appointment_status == 'full':
                    # Tạo payment cho lịch hẹn đang thực hiện
                    payment = Payment.objects.create(
                        appointment=obj,
                        payment_type='exam',
                        total_amount=full,
                        payment_status='paid',
                        payment_method='cash',
                )
                    PaymentDetail.objects.create(
                        payment=payment,
                        service_type='exam',
                        service_id=-1,
                        service_name='Phí khám bệnh',
                        amount=full,
                        detail_quantity=1,
                        detail_status='paid',)
                
                elif obj.appointment_status == 'confirmed':
                    # Tạo payment cho lịch hẹn đã xác nhận
                    if obj.appointment_status == 'full':
                        payment = Payment.objects.create(
                            appointment=obj,
                            payment_type='exam',
                            total_amount=full,
                            payment_status='unpaid',
                            payment_method='banking',
                )
                        PaymentDetail.objects.create(
                            payment=payment,
                            service_type='exam',
                            service_id=-1,
                            service_name='Phí khám bệnh',
                            amount=full,
                            detail_quantity=1,
                            detail_status='unpaid',)



