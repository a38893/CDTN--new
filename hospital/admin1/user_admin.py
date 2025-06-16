

from django.contrib import admin
from django.contrib.auth.hashers import make_password

from hospital.models import Appointment, ProfileDoctor, User

from django import forms
from import_export import resources
from import_export.admin import ImportExportModelAdmin

class UserResource(resources.ModelResource):
    class Meta:
        model = User

class UserAdminForm(forms.ModelForm):
    class Meta:
        model = User
        fields = '__all__'

    def clean_role(self):
        role = self.cleaned_data.get('role')
        user = self.current_user
        if user.role == 'receptionist' and role != 'patient':
            raise forms.ValidationError("Lễ tân chỉ thao tác với tài khoản vai trò bệnh nhân!")
        return role
    
    def __init__(self, *args, **kwargs):
        self.current_user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)
        if 'role' in self.fields and self.current_user and self.current_user.role == 'receptionist':
            self.fields['role'].choices = [('patient', 'Patient')]

class ProfileDoctorInline(admin.TabularInline):
    model = ProfileDoctor
    can_delete = False
    verbose_name_plural = 'Thông tin bác sĩ'
    fk_name = 'user'

    # chỉ cho phép hiển thị inline khi user là bác sĩ
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(user__role='doctor')

class UsersAdmin(ImportExportModelAdmin):
    resource_class = UserResource
    form = UserAdminForm
    list_display = ('user_id', 'username', 'role', 'full_name', 'phone','gmail','status')
    search_fields= ('username','full_name', 'phone', 'gmail','user_id')
    list_filter = ('role',)

    inlines = [ProfileDoctorInline]



    def get_inline_instances(self, request, obj = ...):
        if obj and obj.role == 'doctor':
            return [inline(self.model, self.admin_site) for inline in self.inlines]
        return []
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        class CustomForm(form):
            def __new__(cls, *args, **kwargs2):
                kwargs2['current_user'] = request.user
                return form(*args, **kwargs2)
        return CustomForm
    def save_model(self, request, obj, form, change):
        # Nếu mật khẩu vừa nhập khác với mật khẩu đã hash (hoặc là mật khẩu mới)
        raw_password = form.cleaned_data.get('password')
        if raw_password and not raw_password.startswith('pbkdf2_'):
            obj.password = make_password(raw_password)
        super().save_model(request, obj, form, change)
    
    def get_search_results(self, request, queryset, search_term):
        # Nếu autocomplete cho trường bệnh nhân
        if request.GET.get('field_name') == 'patient_user_id':
            queryset = queryset.filter(role='patient')
        # Nếu autocomplete cho trường bác sĩ
        if request.GET.get('field_name') == 'doctor_user_id':
            queryset = queryset.filter(role='doctor')
        return super().get_search_results(request, queryset, search_term)



    def has_view_permission(self, request, obj=None):
        return request.user.role in ['admin', 'receptionist']

    def has_change_permission(self, request, obj=None):
        return request.user.role in ['admin', 'receptionist']

    def has_delete_permission(self, request, obj=None):
        return request.user.role == 'admin'

    def has_add_permission(self, request):
        return request.user.role in ['admin', 'receptionist']
    
admin.site.register(User, UsersAdmin)