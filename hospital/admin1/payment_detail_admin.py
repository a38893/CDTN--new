from django.contrib import admin
from hospital.models import PaymentDetail



@admin.register(PaymentDetail)
class PaymentDetailAdmin(admin.ModelAdmin):
    # Hiện tất cả các trường của model
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.fields]

    search_fields = ('payment__appointment__appointment_id', 'service_type', 'service_name')
    list_filter = ('service_type',)

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
    