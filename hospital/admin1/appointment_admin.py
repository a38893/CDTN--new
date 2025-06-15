
from django.db import models
from django.contrib import admin
from hospital.models import Appointment, User
from import_export import resources
from import_export.admin import ImportExportModelAdmin


class AppointmentResource(resources.ModelResource):
    class Meta:
        model = Appointment


@admin.register(Appointment)
class AppointmentAdmin(ImportExportModelAdmin):
    resource_class = AppointmentResource
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