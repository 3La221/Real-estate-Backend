from django.contrib import admin
from .models import Tenant, TimeStampedModel, SoftDeleteModel


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    """Admin for Tenant model - each tenant has exactly one agency"""
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
            return self.readonly_fields + ('domain',)
        return self.readonly_fields
