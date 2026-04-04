def tenant_data(request):
    return {
        "current_tenant": getattr(request, "tenant", None),
        "current_agency": getattr(request, "agency", None),
    }