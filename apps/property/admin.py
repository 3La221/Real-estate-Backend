from django import forms
from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
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


def get_user_agency_queryset(user):
    if not getattr(user, "is_authenticated", False):
        return Agency.objects.none()

    if user.is_superuser:
        return Agency.objects.all()

    if not user.is_staff:
        return Agency.objects.none()

    filters = Q(owner=user)
    if getattr(user, "agency_id", None):
        filters |= Q(id=user.agency_id)

    return Agency.objects.filter(filters).distinct()


def get_user_property_queryset(user):
    qs = Property.objects.select_related("agency", "property_type")
    if getattr(user, "is_superuser", False):
        return qs

    return qs.filter(agency__in=get_user_agency_queryset(user))


def user_has_agency_access(user, agency):
    if getattr(user, "is_superuser", False):
        return True
    if not getattr(user, "is_staff", False) or agency is None:
        return False
    return agency.owner_id == user.id or agency.id == getattr(user, "agency_id", None)


def user_has_any_agency_access(user):
    return getattr(user, "is_superuser", False) or get_user_agency_queryset(user).exists()


class PropertyAdminForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        posted_wilaya = self.data.get('wilaya') if hasattr(self, 'data') else None
        if posted_wilaya:
            self.fields['commune'].queryset = Commune.objects.filter(wilaya_id=posted_wilaya)
        elif self.instance and self.instance.pk and self.instance.wilaya_id:
            self.fields['commune'].queryset = Commune.objects.filter(wilaya=self.instance.wilaya)
        else:
            self.fields['commune'].queryset = Commune.objects.none()


class AgencyAdminForm(forms.ModelForm):
    class Meta:
        model = Agency
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        posted_wilaya = self.data.get('wilaya') if hasattr(self, 'data') else None
        if posted_wilaya:
            self.fields['commune'].queryset = Commune.objects.filter(wilaya_id=posted_wilaya)
        elif self.instance and self.instance.pk and self.instance.wilaya_id:
            self.fields['commune'].queryset = Commune.objects.filter(wilaya=self.instance.wilaya)
        else:
            self.fields['commune'].queryset = Commune.objects.none()



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

    def get_model_perms(self, request):
        if request.user.is_superuser:
            return super().get_model_perms(request)
        return {}


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

    def get_model_perms(self, request):
        if request.user.is_superuser:
            return super().get_model_perms(request)
        return {}


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
    form = AgencyAdminForm
    change_form_template = "admin/property_change_form.html"
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
    autocomplete_fields = ("wilaya",)

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

    def has_module_permission(self, request):
        return user_has_any_agency_access(request.user)

    def has_view_permission(self, request, obj=None):
        if obj is None:
            return user_has_any_agency_access(request.user)
        return user_has_agency_access(request.user, obj)

    def has_change_permission(self, request, obj=None):
        if obj is None:
            return user_has_any_agency_access(request.user)
        return user_has_agency_access(request.user, obj)

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(pk__in=get_user_agency_queryset(request.user).values("pk"))

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if obj:
            readonly_fields.append("tenant")
        if not request.user.is_superuser:
            readonly_fields.extend(("tenant", "owner"))
        return tuple(dict.fromkeys(readonly_fields))

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

    def get_model_perms(self, request):
        if request.user.is_superuser:
            return super().get_model_perms(request)
        return {}


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
    form = PropertyAdminForm
    autocomplete_fields = ("agency", "property_type", "wilaya")
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

    def has_module_permission(self, request):
        return user_has_any_agency_access(request.user)

    def has_view_permission(self, request, obj=None):
        if obj is None:
            return user_has_any_agency_access(request.user)
        return user_has_agency_access(request.user, obj.agency)

    def has_change_permission(self, request, obj=None):
        if obj is None:
            return user_has_any_agency_access(request.user)
        return user_has_agency_access(request.user, obj.agency)

    def has_add_permission(self, request):
        return user_has_any_agency_access(request.user)

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related("agency", "property_type")
        
        if request.user.is_superuser:
            return qs
        return qs.filter(agency__in=get_user_agency_queryset(request.user))
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Limit agency choices to agencies the admin user owns or belongs to.
        """
        if db_field.name == "agency":
            if not request.user.is_superuser:
                user_agencies = get_user_agency_queryset(request.user)
                kwargs["queryset"] = user_agencies
                first_agency = user_agencies.first()
                if first_agency:
                    kwargs["initial"] = first_agency
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def save_model(self, request, obj, form, change):
        """
        Prevent non-superusers from saving a property under another agency.
        """
        if not request.user.is_superuser:
            user_agencies = get_user_agency_queryset(request.user)
            if not user_agencies.exists():
                raise PermissionDenied("You do not have access to an agency.")
            if obj.agency_id and not user_agencies.filter(pk=obj.agency_id).exists():
                raise PermissionDenied("You cannot assign properties to another agency.")
            if not obj.agency_id:
                obj.agency = user_agencies.first()
        
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

    change_form_template = "admin/property_change_form.html"



@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    search_fields = ("name",)

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_staff

    def get_model_perms(self, request):
        if request.user.is_superuser:
            return super().get_model_perms(request)
        return {}



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
        property_qs = get_user_property_queryset(request.user)
        agency_qs = get_user_agency_queryset(request.user)
        context['dashboard_cards'] = [
            {
                "title": "Total Properties",
                "value": property_qs.count(),
                "icon": "fas fa-building",
                "color": "bg-primary",
                "url": "/admin/property/property/",
            },
            {
                "title": "Active Properties",
                "value": property_qs.filter(status="active").count(),
                "icon": "fas fa-check-circle",
                "color": "bg-success",
                "url": "/admin/property/property/?status=active",
            },
            {
                "title": "Sold Properties",
                "value": property_qs.filter(status="sold").count(),
                "icon": "fas fa-dollar-sign",
                "color": "bg-danger",
                "url": "/admin/property/property/?status=sold",
            },
            {
                "title": "Rented Properties",
                "value": property_qs.filter(status="rented").count(),
                "icon": "fas fa-key",
                "color": "bg-info",
                "url": "/admin/property/property/?status=rented",
            },
            {
                "title": "Total Agencies",
                "value": agency_qs.count(),
                "icon": "fas fa-users",
                "color": "bg-warning",
                "url": "/admin/property/agency/",
            },
        ]
        context['latest_properties'] = property_qs.order_by("-created_at")[:5]
        return context
