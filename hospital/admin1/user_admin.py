

from django.contrib import admin
from django.contrib.auth.hashers import make_password

from hospital.models import Appointment, User

from django import forms


class UserAdminForm(forms.ModelForm):
    class Meta:
        model = User
        fields = '__all__'

    def clean_role(self):
        role = self.cleaned_data.get('role')
        user = self.current_user

        if user.role == 'receptionist' and role != 'patient':
            raise forms.ValidationError("Lễ tân chỉ tạo được tài khoản với vai trò lễ tân!")
        return role
    
    def __init__(self, *args, **kwargs):
        self.current_user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)
        if self.current_user and self.current_user.role == 'receptionist':
            self.fields['role'].choices = [('patient', 'Patient')]

class UsersAdmin(admin.ModelAdmin):
    form = UserAdminForm
    list_display = ('user_id', 'username', 'role', 'full_name', 'phone','gmail')
    search_fields= ('username','full_name', 'phone', 'gmail','user_id')
    list_filter = ('role',)
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
    

    def has_view_permission(self, request, obj=None):
        return request.user.role in ['admin', 'receptionist']

    def has_change_permission(self, request, obj=None):
        return request.user.role == 'admin'

    def has_delete_permission(self, request, obj=None):
        return request.user.role == 'admin'

    def has_add_permission(self, request):
        return request.user.role in ['admin', 'receptionist']
    
admin.site.register(User, UsersAdmin)