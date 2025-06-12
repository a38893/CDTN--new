from django.contrib import admin
from hospital.models import PatientTest, LabTest, Appointment, User



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
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.test_status in ['Pending', 'Done']:
            return [field.name for field in self.model._meta.fields]
        return super().get_readonly_fields(request, obj)