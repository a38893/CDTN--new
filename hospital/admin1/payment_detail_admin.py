from django.contrib import admin
from hospital.models import PaymentDetail
from import_export import resources
from import_export.admin import ImportExportModelAdmin

class PaymentDetailResource(resources.ModelResource):
    class Meta:
        model = PaymentDetail
@admin.register(PaymentDetail)
class PaymentDetailAdmin(ImportExportModelAdmin):
    resource_class = PaymentDetailResource
    # Hiện tất cả các trường của model
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.fields]

    search_fields = ('payment__appointment__appointment_id', 'service_type', 'service_name')
    list_filter = ('service_type',)
    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        # Nếu search_term là số, tìm theo payment_id (ForeignKey)
        if search_term.isdigit():
            queryset |= self.model.objects.filter(payment__payment_id=int(search_term))
        return queryset, use_distinct
    def has_view_permission(self, request, obj=None):
        # Lễ tân và admin đều xem được
        return request.user.role in ['admin', 'receptionist']

    def has_change_permission(self, request, obj=None):
        # Chỉ admin được sửa
        return request.user.role == 'admin'

    def has_add_permission(self, request):
        # Chỉ admin được thêm
        return request.user.role == 'admin'

    def has_delete_permission(self, request, obj=None):
        # Chỉ admin được xóa
        return request.user.role == 'admin'

    def get_readonly_fields(self, request, obj=None):
        # Lễ tân luôn readonly tất cả trường
        if request.user.role == 'receptionist':
            return [field.name for field in self.model._meta.fields]
        return super().get_readonly_fields(request, obj)
    