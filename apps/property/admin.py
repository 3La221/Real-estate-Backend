from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import (
    Agency, AgencyContact, PropertyType, Property, PropertyMedia,
    Amenity, PropertyAmenity, Wilaya, Commune
)
from django.contrib.admin import AdminSite
from django.urls import path
from django.shortcuts import render
from .models import Property, Agency


# -------------------------
# 1️⃣ Wilaya & Commune Admin
# -------------------------
@admin.register(Wilaya)
class WilayaAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(Commune)
class CommuneAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    autocomplete_fields = ("wilaya",)


# -------------------------
# 2️⃣ Agency & Contacts Admin
# -------------------------
class AgencyContactInline(admin.TabularInline):
    model = AgencyContact
    extra = 1
    readonly_fields = ("is_primary",)
    fields = ("type", "number", "label", "is_primary")


@admin.register(Agency)
class AgencyAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "wilaya", "commune", "email", "is_active", "created_at")
    list_filter = ("is_active", "wilaya")
    search_fields = ("name", "owner__username", "email")
    readonly_fields = ("created_at",)
    inlines = [AgencyContactInline]
    autocomplete_fields = ("wilaya", "commune")
    fieldsets = (
        ("Basic Info", {"fields": ("owner", "name", "slug", "description", "email")}),
        ("Location", {"fields": ("wilaya", "commune", "address")}),
        ("Media & Social", {"fields": ("logo", "cover_image", "facebook", "instagram", "tiktok")}),
        ("Status & Meta", {"fields": ("is_active", "created_at")}),
    )


# -------------------------
# 3️⃣ Property Type Admin
# -------------------------
@admin.register(PropertyType)
class PropertyTypeAdmin(admin.ModelAdmin):
    search_fields = ("name",)


# -------------------------
# 4️⃣ Property Media & Amenity Inlines
# -------------------------
class PropertyMediaInline(admin.TabularInline):
    model = PropertyMedia
    extra = 1
    readonly_fields = ("is_cover",)
    fields = ("image", "order", "is_cover")


class PropertyAmenityInline(admin.TabularInline):
    model = PropertyAmenity
    extra = 1
    autocomplete_fields = ("amenity",)


# -------------------------
# 5️⃣ Property Admin
# -------------------------
@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = (
        "title", "agency", "property_type", "listing_type",
        "status_badge", "price", "views_count", "leads_count",
        "is_featured", "is_published", "created_at"
    )
    list_filter = (
        "status", "listing_type", "property_type", "wilaya",
        "is_featured", "is_published"
    )
    search_fields = ("title", "reference", "agency__name")
    autocomplete_fields = ("agency", "property_type", "wilaya", "commune")
    readonly_fields = (
        "reference", "views_count", "leads_count",
        "created_at", "updated_at"
    )
    prepopulated_fields = {"slug": ("title",)}
    inlines = [PropertyMediaInline, PropertyAmenityInline]

    fieldsets = (
        ("Basic", {"fields": ("agency", "title", "slug", "description")}),
        ("Type & Status", {"fields": ("property_type", "listing_type", "status")}),
        ("Price", {"fields": ("price", "negotiable", "available_from")}),
        ("Location", {"fields": ("wilaya", "commune", "address", "latitude", "longitude")}),
        ("Details", {"fields": ("area_m2", "bedrooms", "bathrooms", "floor")}),
        ("Extras", {"fields": ("furnished", "parking")}),
        ("Portfolio", {"fields": ("is_published", "is_featured")}),
        ("Analytics", {"fields": ("views_count", "leads_count")}),
    )

    actions = ["publish_properties", "archive_properties", "mark_as_sold", "mark_as_rented"]

    # -------------------------
    # Status Badge
    # -------------------------
    def status_badge(self, obj):
        colors = {
            "draft": "gray",
            "active": "green",
            "sold": "red",
            "rented": "blue",
            "archived": "black",
        }
        return format_html(
            '<span style="color:{}; font-weight:bold;">{}</span>',
            colors.get(obj.status, "black"),
            obj.get_status_display()
        )
    status_badge.short_description = "Status"

    # -------------------------
    # Custom Actions
    # -------------------------
    @admin.action(description="Publish selected properties")
    def publish_properties(self, request, queryset):
        queryset.update(status=Property.ACTIVE, is_published=True)

    @admin.action(description="Archive selected properties")
    def archive_properties(self, request, queryset):
        queryset.update(status=Property.ARCHIVED, is_published=False)

    @admin.action(description="Mark selected properties as Sold")
    def mark_as_sold(self, request, queryset):
        queryset.update(status=Property.SOLD, is_published=False)

    @admin.action(description="Mark selected properties as Rented")
    def mark_as_rented(self, request, queryset):
        queryset.update(status=Property.RENTED, is_published=False)

    # -------------------------
    # Multi-Tenant: Limit queryset
    # -------------------------
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(agency__owner=request.user)

    # -------------------------
    # Multi-Tenant: Auto-assign agency
    # -------------------------
    def save_model(self, request, obj, form, change):
        if not change and not obj.agency_id:
            obj.agency = request.user.agencies.first()
        super().save_model(request, obj, form, change)


# -------------------------
# 6️⃣ Amenity Admin
# -------------------------
@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    search_fields = ("name",)


# -------------------------
# 7️⃣ Dashboard Cards for Jazzmin
# -------------------------
# Jazzmin automatically detects `index_template` override.
# You can add cards via context processor in your templates, or simply configure with custom templates.
# URLs should use Django's reverse() directly.

# Example usage in custom template:
#   {% for card in dashboard_cards %}
#     <div class="card {{ card.color }}">
#       <i class="{{ card.icon }}"></i>
#       <span>{{ card.title }}</span>
#       <span>{{ card.value }}</span>
#     </div>
#   {% endfor %}
class DashboardAdminSite(AdminSite):
    site_header = "Real Estate Admin"
    site_title = "RE Admin Dashboard"
    index_title = "Dashboard"
    index_template = "admin/custom_index.html"

    def get_urls(self):
        urls = super().get_urls()
        # You can add custom views here if needed
        return urls

    def each_context(self, request):
        context = super().each_context(request)
        # Quick Stats Cards
        context['dashboard_cards'] = [
            {
                "title": "Total Properties",
                "value": Property.objects.count(),
                "icon": "fas fa-building",
                "color": "bg-primary",
                "url": "/admin/property/property/",
            },
            {
                "title": "Active Properties",
                "value": Property.objects.filter(status="active").count(),
                "icon": "fas fa-check-circle",
                "color": "bg-success",
                "url": "/admin/property/property/?status=active",
            },
            {
                "title": "Sold Properties",
                "value": Property.objects.filter(status="sold").count(),
                "icon": "fas fa-dollar-sign",
                "color": "bg-danger",
                "url": "/admin/property/property/?status=sold",
            },
            {
                "title": "Rented Properties",
                "value": Property.objects.filter(status="rented").count(),
                "icon": "fas fa-key",
                "color": "bg-info",
                "url": "/admin/property/property/?status=rented",
            },
            {
                "title": "Total Agencies",
                "value": Agency.objects.count(),
                "icon": "fas fa-users",
                "color": "bg-warning",
                "url": "/admin/property/agency/",
            },
        ]
        # Latest 5 properties
        context['latest_properties'] = Property.objects.order_by("-created_at")[:5]
        return context

# Then replace default admin site:
admin_site = DashboardAdminSite(name='dashboard')

# Register all models with your custom admin_site instead of admin.site
admin_site.register(Property, PropertyAdmin)
admin_site.register(Agency, AgencyAdmin)
admin_site.register(PropertyType, PropertyTypeAdmin)
admin_site.register(Wilaya, WilayaAdmin)
admin_site.register(Commune, CommuneAdmin)
admin_site.register(Amenity, AmenityAdmin)
