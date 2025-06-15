from django.contrib import admin
from hospital.models import Prescription, User
from import_export import resources
from import_export.admin import ImportExportModelAdmin

class PrescriptionResource(resources.ModelResource):
    class Meta:
        model = Prescription

@admin.register(Prescription)
class PrescriptionAdmin(ImportExportModelAdmin):
    resource_class = PrescriptionResource
    list_display = (
        'prescription_id',
        # 'duration',
        # 'dosage',
        'prescription_quantity',
        # 'instructions',
        # 'frequency',
        'medication',
        'record'
    )
    search_fields = ('medication__medication_name',)
    list_filter = ('record',)
    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        if search_term.isdigit():
            queryset |= self.model.objects.filter(record_id=int(search_term))
        return queryset, use_distinct


    def has_view_permission(self, request, obj=None):
        return request.user.role in ['admin', 'receptionist', 'doctor']

    def has_change_permission(self, request, obj=None):
        return request.user.role in ['admin', 'doctor']

    def has_add_permission(self, request):
        return request.user.role in ['admin', 'doctor']

    def has_delete_permission(self, request, obj=None):
        return request.user.role in ['admin']

