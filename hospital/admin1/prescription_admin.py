from django.contrib import admin
from hospital.models import PaymentDetail, Prescription, PrescriptionDetail, User, Medication, Payment
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from django import forms
from django.utils import timezone
class PrescriptionResource(resources.ModelResource):
    class Meta:
        model = Prescription


class PrescriptionDetailInlineForm(forms.ModelForm):
    class Meta:
        model = PrescriptionDetail
        fields = '__all__'

    def has_add_permission(self, request, obj):
        if obj and obj.prescription_status == 'done':
            return False
        return super().has_add_permission(request, obj)

    def has_change_permission(self, request, obj=None):
        if obj and obj.prescription_status == 'done':
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.prescription_status == 'done':
            return False
        return super().has_delete_permission(request, obj)
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
        return request.user.role in ['admin', 'doctor', 'receptionist'] 

    def has_add_permission(self, request):
        return request.user.role in ['admin', 'doctor']

    def has_delete_permission(self, request, obj=None):
        return request.user.role in ['admin']

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        self.create_payment(obj)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        self.create_payment(form.instance)

    def create_payment(self, prescription):
        appointment = prescription.record.appointment
        total_amount = sum(
            detail.medication.medication_price * detail.quantity for detail in prescription.details.all()
        )
        payment, created = Payment.objects.get_or_create(
            appointment=appointment,
            payment_type='prescription',
            defaults={
                'total_amount': total_amount,
                'payment_status': 'unpaid',
                'payment_method': '',
                'payment_timestamp': timezone.now()
            }
        )
        if not created:
            payment.total_amount = total_amount
            payment.save()
        for detail in prescription.details.all():
            PaymentDetail.objects.get_or_create(
                payment=payment,
                service_type='prescription',
                service_id=detail.medication.pk,
                service_name=str(detail),
                amount=detail.medication.medication_price ,
                detail_quantity=detail.quantity,
                detail_status='unpaid'
            )


# Khi thanh toán thành công chỉ có thể update trạng thái sang done
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj and obj.prescription_status in ['paid']:
            form.base_fields['prescription_status'].choices = [
                ('paid', 'Đã thanh toán'),
                ('done', 'Đã xong (hoàn tất)'),
            ]
        return form

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.prescription_status  =='done':
            return [f.name for f in self.model._meta.fields if f.name != 'prescription_id']
        return super().get_readonly_fields(request, obj)