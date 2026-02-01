from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom admin for User model"""
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'agency', 'phone_number']
    list_filter = BaseUserAdmin.list_filter + ('agency',)
    search_fields = ['username', 'email', 'first_name', 'last_name', 'agency__name']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Agency Assignment', {
            'fields': ('agency',),
            'description': 'Assign user to an agency. Agency staff can only manage their own agency properties.'
        }),
        ('Additional Info', {'fields': ('phone_number',)}),
    )
    
    def get_queryset(self, request):
        """Superadmins see all users, agency staff only see their agency users"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Agency staff can see users from their agency
        if hasattr(request.user, 'agency') and request.user.agency:
            return qs.filter(agency=request.user.agency)
        return qs.none()
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Limit agency selection for non-superusers"""
        if db_field.name == 'agency':
            if not request.user.is_superuser:
                # Agency staff can only assign to their own agency
                if hasattr(request.user, 'agency') and request.user.agency:
                    kwargs['queryset'] = request.user.agency.__class__.objects.filter(
                        id=request.user.agency.id
                    )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
