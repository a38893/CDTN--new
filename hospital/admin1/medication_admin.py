from django.contrib import admin
from hospital.models import Medication
from import_export import resources
from import_export.admin import ImportExportModelAdmin


class MedicationResource(resources.ModelResource):
    class Meta:
        model = Medication
@admin.register(Medication)
class MedicationAdmin(ImportExportModelAdmin):
    resource_class = MedicationResource
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
    