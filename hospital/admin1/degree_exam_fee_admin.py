from django.contrib import admin
from hospital.models import DegreeExamFee

class DegreeExamFeeAdmin(admin.ModelAdmin):
    list_display = ('degree_id', 'degree_name', 'fee')
    search_fields = ('degree_name',)
    list_editable = ('degree_name', 'fee')
    ordering = ('degree_id',)
    list_per_page = 20

admin.site.register(DegreeExamFee, DegreeExamFeeAdmin)