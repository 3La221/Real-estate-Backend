

from rest_framework import permissions


class TenantPermission(permissions.BasePermission):

    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return hasattr(request, 'tenant') and request.tenant is not None
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            if hasattr(obj, 'agency'):
                return obj.agency.tenant_id == request.tenant.id
            return False
        
        if not request.user.is_authenticated:
            return False
        
        if hasattr(obj, 'agency'):
            return obj.agency.tenant_id == request.tenant.id
        return False

