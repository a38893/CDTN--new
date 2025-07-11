from django.contrib import admin
from hospital.models import LabTest
from import_export import resources
from import_export.admin import ImportExportModelAdmin
class LabTestResource(resources.ModelResource):
    class Meta:
        model = LabTest

@admin.register(LabTest)
class LabTestAdmin(ImportExportModelAdmin):
    resource_class = LabTestResource
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
    