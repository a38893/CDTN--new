from django.contrib import admin
from hospital.models import Payment, Appointment
from import_export import resources
from import_export.admin import ImportExportModelAdmin

class PaymentResource(resources.ModelResource):
    class Meta:
        model = Payment

@admin.register(Payment)
class PaymentAdmin(ImportExportModelAdmin):
    resource_class = PaymentResource
    list_display = ('payment_id', 'appointment', 'total_amount', 'payment_status', 'payment_method', 'payment_timestamp', 'payment_type')
    search_fields = ('payment_id','appointment__appointment_id', 'payment_status', 'payment_method')
    list_filter = ('payment_status', 'payment_method')
    def has_view_permission(self, request, obj=None):
        # Admin, lễ tân, bác sĩ đều xem được
        return request.user.role in ['admin', 'receptionist']

    def has_change_permission(self, request, obj=None):
        # Admin và lễ tân được sửa
        return request.user.role in ['admin', 'receptionist']

    def has_add_permission(self, request):
        # Admin và lễ tân được thêm
        return request.user.role in ['admin', 'receptionist']

    def has_delete_permission(self, request, obj=None):
        # Admin và lễ tân được xóa
        return request.user.role in ['admin']
    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        # Nếu đã paid thì tất cả các trường đều readonly
        if obj and obj.payment_status == 'paid':
            # Lấy tất cả các trường trừ id
            all_fields = [f.name for f in self.model._meta.fields if f.name != 'payment_id']
            return readonly + all_fields
        return readonly

    def has_delete_permission(self, request, obj=None):
        # Không cho phép xóa nếu đã paid
        if obj and obj.payment_status == 'paid':
            return False
        return super().has_delete_permission(request, obj)
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Nếu là lễ tân, chỉ cho phép chỉnh sửa payment_status (nếu cần logic này, hãy kiểm soát ở form hoặc readonly_fields)
        # Đồng bộ trạng thái chi tiết thanh toán
        if obj.payment_status == 'paid':
            obj.details.update(detail_status='paid')
        elif obj.payment_status in ['unpaid', 'pending']:
            obj.details.update(detail_status='unpaid')