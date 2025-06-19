from django.contrib import admin
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.token_blacklist.admin import BlacklistedTokenAdmin, OutstandingTokenAdmin

class AdminOnlyOutstandingTokenAdmin(OutstandingTokenAdmin):
    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

class AdminOnlyBlacklistedTokenAdmin(BlacklistedTokenAdmin):
    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

# Unregister mặc định và đăng ký lại với quyền mới
try:
    admin.site.unregister(OutstandingToken)
except admin.sites.NotRegistered:
    pass
admin.site.register(OutstandingToken, AdminOnlyOutstandingTokenAdmin)

try:
    admin.site.unregister(BlacklistedToken)
except admin.sites.NotRegistered:
    pass
admin.site.register(BlacklistedToken, AdminOnlyBlacklistedTokenAdmin)