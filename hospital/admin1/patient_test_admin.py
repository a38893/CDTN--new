from django.contrib import admin
from hospital.models import PatientTest, LabTest, Appointment, User
from import_export import resources
from import_export.admin import ImportExportModelAdmin

class PatientTestResource(resources.ModelResource):
    class Meta:
        model = PatientTest

@admin.register(PatientTest)
class PatientTestAdmin(ImportExportModelAdmin):
    resource_class = PatientTestResource
    list_display = ('patient_test_id', 'record','test_result', 'test', 'test_date', 'test_status', 'performed_by_doctor', 'get_appointment_id')
    search_fields = ('record__appointment__appointment_id', 'test__test_name', 'performed_by_doctor__username')
    list_filter = ('test_status', 'test__test_category')
    def get_appointment_id(self, obj):
        return obj.record.appointment.appointment_id if obj.record and obj.record.appointment else None
    get_appointment_id.short_description = 'Mã lịch hẹn'
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
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.test_status in ['Pending', 'Done']:
            return [field.name for field in self.model._meta.fields]
        return super().get_readonly_fields(request, obj)
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        user = request.user
        if 'performed_by_doctor' in form.base_fields and hasattr(form.base_fields['performed_by_doctor'], 'queryset'):
            form.base_fields['performed_by_doctor'].queryset = User.objects.filter(pk=user.pk)
        return form