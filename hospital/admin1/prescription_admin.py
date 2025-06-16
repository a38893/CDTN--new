from django.contrib import admin
from hospital.models import Prescription, PrescriptionDetail, User, Medication
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from django import forms
class PrescriptionResource(resources.ModelResource):
    class Meta:
        model = Prescription


class PrescriptionDetailInlineForm(forms.ModelForm):
    class Meta:
        model = PrescriptionDetail
        fields = '__all__'


    def clean(self):
        cleaned_data = super().clean()
        medication = cleaned_data.get('medication')
        quantity = cleaned_data.get('quantity')
        if medication and quantity is not None:
            if quantity > medication.stock_quantity:
                raise forms.ValidationError(
                    f"Số lượng kê ({quantity}) vượt quá tồn kho ({medication.stock_quantity}) của thuốc {medication.medication_name}."
                )
        return cleaned_data


class PrescriptionDetailInline(admin.TabularInline):
    model = PrescriptionDetail
    form = PrescriptionDetailInlineForm
    extra = 1
    autocomplete_fields = ('medication',)

@admin.register(Prescription)
class PrescriptionAdmin(ImportExportModelAdmin):
    resource_class = PrescriptionResource
    inlines = [PrescriptionDetailInline]
    list_display = (
        'prescription_id',
        'record',
        'prescription_status',
        'instructions',
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

