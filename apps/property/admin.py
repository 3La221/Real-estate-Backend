from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from adminsortable2.admin import SortableAdminMixin, SortableInlineAdminMixin,SortableAdminBase
from .models import (
    Agency, AgencyContact, PropertyType, Property, PropertyMedia,
    Amenity, PropertyAmenity, Wilaya, Commune
)
from django.contrib.admin import AdminSite
from django.urls import path
from django.shortcuts import render
from .models import Property, Agency



@admin.register(Wilaya)
class WilayaAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_display = ("id", "name")
    
    def has_add_permission(self, request):
        """Only superusers can add wilayas"""
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        """Only superusers can change wilayas"""
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete wilayas"""
        return request.user.is_superuser
    
    def has_view_permission(self, request, obj=None):
        """Everyone with staff status can view wilayas (needed for dropdowns)"""
        return request.user.is_staff


@admin.register(Commune)
class CommuneAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    autocomplete_fields = ("wilaya",)
    list_display = ("id", "name", "wilaya")
    list_filter = ("wilaya",)
    
    def has_add_permission(self, request):
        """Only superusers can add communes"""
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        """Only superusers can change communes"""
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete communes"""
        return request.user.is_superuser
    
    def has_view_permission(self, request, obj=None):
        """Everyone with staff status can view communes (needed for dropdowns)"""
        return request.user.is_staff


# -------------------------
# 2️⃣ Agency & Contacts Admin
# -------------------------
from django.contrib import admin
from django.utils.html import format_html
from django.db import models
from .models import Agency, AgencyContact

class AgencyContactInline(admin.TabularInline):
    model = AgencyContact
    extra = 1
    fields = ("type", "number", "label", "is_primary")
    ordering = ("-is_primary", "id")


@admin.register(Agency)
class AgencyAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "tenant",
        "owner",
        "wilaya",
        "commune",
        "email",
        "staff_count",
        "is_active",
        "created_at",
        "primary_color_display",
    )
    list_filter = ("is_active", "wilaya")
    search_fields = ("name", "owner__username", "email", "tagline")
    readonly_fields = (
        "created_at",
        "staff_count",
        "slug",
        "logo_preview",
        "cover_preview",
        "hero_preview",
        "about_us_preview",
        "google_maps_preview",
    )
    inlines = [AgencyContactInline]
    autocomplete_fields = ("wilaya", "commune")

    fieldsets = (
        ("Tenant (One Agency Per Tenant)", {
            "fields": ("tenant",),
            "description": "Each tenant has exactly one agency. Tenant cannot be changed after creation."
        }),
        ("Owner", {"fields": ("owner",)}),
        ("Basic Info", {"fields": ("name", "slug", "description", "email", "tagline")}),
        ("Location", {"fields": ("wilaya", "commune", "address", "google_maps_url", "google_maps_preview")}),
        ("Branding & Media", {
            "fields": (
                "logo", "logo_preview",
                "cover_image", "cover_preview",
                "hero_title", "hero_subtitle",
                "hero_image", "hero_preview",
                "about_us_title",
                "about_us_image","about_us_preview",
                "primary_color", "secondary_color","accent_color","navbar_background_color",
            )
        }),
        ("Footer", {"fields": ("footer_description",)}),
        ("Social Media", {"fields": ("facebook", "instagram", "tiktok")}),
        ("Status & Meta", {"fields": ("is_active", "staff_count", "created_at")}),
    )

    # Previews for media fields
    def logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" style="max-width:100px; max-height:100px;" />', obj.logo.url)
        return "-"
    logo_preview.short_description = "Logo Preview"

    def about_us_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" style="max-width:100px; max-height:100px;" />', obj.about_us_image.url)
        return "-"
    logo_preview.short_description = "Logo Preview"

    def cover_preview(self, obj):
        if obj.cover_image:
            return format_html('<img src="{}" style="max-width:150px; max-height:80px;" />', obj.cover_image.url)
        return "-"
    cover_preview.short_description = "Cover Preview"

    def hero_preview(self, obj):
        if obj.hero_image:
            return format_html('<img src="{}" style="max-width:200px; max-height:120px;" />', obj.hero_image.url)
        return "-"
    hero_preview.short_description = "Hero Image Preview"

    # Google Maps preview link
    def google_maps_preview(self, obj):
        if obj.google_maps_url:
            return format_html('<iframe src="{}" width="400" height="300" style="border:0;" allowfullscreen="" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe>', obj.google_maps_url)
        return "-"
    google_maps_preview.short_description = "Map Preview"

    # Color preview
    def primary_color_display(self, obj):
        if obj.primary_color:
            return format_html(
                '<div style="width:20px; height:20px; border:1px solid #000; background-color:{};"></div>',
                obj.primary_color
            )
        return "-"
    primary_color_display.short_description = "Primary Color"

    # Staff count helper
    def staff_count(self, obj):
        count = obj.staff_users.count()
        if count > 0:
            url = f"/admin/accounts/user/?agency__id__exact={obj.id}"
            return format_html('<a href="{}">{} staff</a>', url, count)
        return "0 staff"
    staff_count.short_description = "Staff Users"

    # Restrict add permissions for existing tenants
    def has_add_permission(self, request):
        if request.user.is_superuser:
            return True
        return False

    # Filter queryset for agency staff
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if hasattr(request.user, "agency") and request.user.agency:
            return qs.filter(id=request.user.agency.id)
        return qs.none()

    # Make tenant readonly after creation
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing existing agency
            return self.readonly_fields + ("tenant",)
        return self.readonly_fields

    # Optional: make color picker for primary & secondary colors
    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name in ("primary_color", "secondary_color","accent_color","navbar_background_color",):
            kwargs["widget"] = kwargs.get("widget", admin.widgets.AdminTextInputWidget(attrs={"type": "color"}))
        return super().formfield_for_dbfield(db_field, **kwargs)
# -------------------------
# 3️⃣ Property Type Admin
# -------------------------
@admin.register(PropertyType)
class PropertyTypeAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_display = ("name", "slug")
    
    def has_add_permission(self, request):
        """Only superusers can add property types"""
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        """Only superusers can change property types"""
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete property types"""
        return request.user.is_superuser
    
    def has_view_permission(self, request, obj=None):
        """Everyone with staff status can view property types (needed for dropdowns)"""
        return request.user.is_staff


# -------------------------
# 4️⃣ Property Media & Amenity Inlines
# -------------------------
class PropertyMediaInline(admin.TabularInline):
    model = PropertyMedia
    extra = 1
    fields = ("image_preview", "image", "order", "is_cover")
    readonly_fields = ("image_preview",)


    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="height: 80px; width: auto; border-radius:5px;" />',
                obj.image.url
            )
        return "-"
    
    image_preview.short_description = "Preview"

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
        "is_featured", "is_published", "agency__tenant"
    )
    search_fields = ("title", "reference", "agency__name", "address")
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
        ("Analytics", {"fields": ("views_count", "leads_count", "reference", "created_at", "updated_at")}),
    )

    actions = ["publish_properties", "archive_properties", "mark_as_sold", "mark_as_rented", "feature_properties"]
    
    def get_queryset(self, request):
        
        qs = super().get_queryset(request)
        
        if request.user.is_superuser:
            return qs
        
        if hasattr(request.user, 'agency') and request.user.agency:
            return qs.filter(agency=request.user.agency)
        
        try:
            user_agency = Agency.objects.get(owner=request.user)
            return qs.filter(agency=user_agency)
        except Agency.DoesNotExist:
            return qs.none()
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Auto-select agency for agency staff users.
        """
        if db_field.name == "agency":
            if not request.user.is_superuser:
                if hasattr(request.user, 'agency') and request.user.agency:
                    kwargs["queryset"] = Agency.objects.filter(id=request.user.agency.id)
                    kwargs["initial"] = request.user.agency
                else:

                    try:
                        user_agency = Agency.objects.get(owner=request.user)
                        kwargs["queryset"] = Agency.objects.filter(id=user_agency.id)
                        kwargs["initial"] = user_agency
                    except Agency.DoesNotExist:
                        kwargs["queryset"] = Agency.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def save_model(self, request, obj, form, change):
        """
        Auto-assign agency for non-superusers (one agency per tenant).
        """
        if not change and not request.user.is_superuser:
            # For new properties, auto-assign user's agency
            try:
                user_agency = Agency.objects.get(owner=request.user)
                if not obj.agency:
                    obj.agency = user_agency
            except Agency.DoesNotExist:
                pass
        
        super().save_model(request, obj, form, change)

   
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

    @admin.action(description="✅ Publish selected properties")
    def publish_properties(self, request, queryset):
        updated = queryset.update(status=Property.ACTIVE, is_published=True)
        self.message_user(request, f"{updated} properties published successfully.")

    @admin.action(description="📦 Archive selected properties")
    def archive_properties(self, request, queryset):
        updated = queryset.update(status=Property.ARCHIVED, is_published=False)
        self.message_user(request, f"{updated} properties archived successfully.")

    @admin.action(description="💰 Mark selected properties as Sold")
    def mark_as_sold(self, request, queryset):
        updated = queryset.update(status=Property.SOLD, is_published=False)
        self.message_user(request, f"{updated} properties marked as sold.")

    @admin.action(description="🏠 Mark selected properties as Rented")
    def mark_as_rented(self, request, queryset):
        updated = queryset.update(status=Property.RENTED, is_published=False)
        self.message_user(request, f"{updated} properties marked as rented.")
    
    @admin.action(description="⭐ Feature selected properties")
    def feature_properties(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f"{updated} properties marked as featured.")

    # change_form_template = "admin/property_change_form.html"



@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    search_fields = ("name",)



class DashboardAdminSite(AdminSite):
    site_header = "Real Estate Admin"
    site_title = "RE Admin Dashboard"
    index_title = "Dashboard"
    index_template = "admin/custom_index.html"

    def get_urls(self):
        urls = super().get_urls()
        return urls

    def each_context(self, request):
        context = super().each_context(request)
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
        context['latest_properties'] = Property.objects.order_by("-created_at")[:5]
        return context
