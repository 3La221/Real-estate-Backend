from apps.property.models import Agency


class TenantFilterMixin:
    """Mixin to filter queryset by tenant"""
    
    def get_queryset(self):
        """Filter queryset to only include objects belonging to current tenant"""
        queryset = super().get_queryset()
        
        if hasattr(self.request, 'tenant') and self.request.tenant:
            queryset = queryset.filter(agency__tenant=self.request.tenant)
        
        return queryset
    
    def get_tenant_agency(self):
        """Get the single agency for the current tenant"""
        if hasattr(self.request, 'tenant') and self.request.tenant:
            try:
                return Agency.objects.get(
                    tenant=self.request.tenant,
                    is_active=True
                )
            except Agency.DoesNotExist:
                return None
        return None