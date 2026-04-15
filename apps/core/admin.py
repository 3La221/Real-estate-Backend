from django import forms
from django.contrib import admin
from .models import Tenant, TimeStampedModel, SoftDeleteModel


class TenantAdminForm(forms.ModelForm):
    additional_domains = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
        help_text='Enter one domain per line (e.g. app.example.com)'
    )

    class Meta:
        model = Tenant
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and isinstance(self.instance.additional_domains, list):
            self.fields['additional_domains'].initial = '\n'.join(self.instance.additional_domains)

    def clean_additional_domains(self):
        raw = self.cleaned_data.get('additional_domains', '')
        domains = [d.strip() for d in raw.replace(',', '\n').splitlines() if d.strip()]
        return domains


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    """Admin for Tenant model - each tenant has exactly one agency"""
    form = TenantAdminForm
    list_display = ['name', 'domain', 'slug', 'has_agency', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'domain', 'slug']
    readonly_fields = ['created_at', 'updated_at', 'agency_info']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'is_active')
        }),
        ('Domain Configuration', {
            'fields': ('domain', 'additional_domains')
        }),
        ('Agency (One-to-One)', {
            'fields': ('agency_info',),
            'description': 'Each tenant has exactly one agency. Create agency after creating tenant.'
        }),
        ('Advanced', {
            'fields': ('schema_name',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_agency(self, obj):
        try:
            return '✅ Yes' if obj.agency else '❌ No'
        except:
            return '❌ No'
    has_agency.short_description = 'Has Agency'
    
    def agency_info(self, obj):
        """Display agency information"""
        try:
            agency = obj.agency
            return f"Agency: {agency.name} (Owner: {agency.owner.username})"
        except:
            return "No agency created yet. Create one in Property → Agencies"
    agency_info.short_description = 'Agency Information'
    
    def get_readonly_fields(self, request, obj=None):
        """Make domain read-only after creation for safety"""
        if obj: 
            return self.readonly_fields + ['domain']
        return self.readonly_fields
