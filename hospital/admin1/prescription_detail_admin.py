from django.contrib import admin
from hospital.models import Prescription, PrescriptionDetail, Medication
@admin.register(PrescriptionDetail)
class PrescriptionDetailAdmin(admin.ModelAdmin):
    list_display = ['detail_id', 'prescription', 'medication', 'quantity', 'dosage', 'display_recommended_dosage']
    search_fields = ['medication__medication_name', 'dosage']
    list_filter = ['prescription__prescription_status', 'medication__medication_category']

    def display_recommended_dosage(self, obj):
        return obj.medication.recommended_dosage
    display_recommended_dosage.short_description = 'Liều lượng khuyến nghị'