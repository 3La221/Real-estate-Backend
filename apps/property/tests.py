from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.test import RequestFactory, TestCase
from django.urls import resolve
from unittest.mock import patch

from apps.accounts.models import User
from apps.core.models import Tenant
from apps.property.models import (
    Agency,
    Amenity,
    Commune,
    Property,
    PropertyAmenity,
    PropertyType,
    Wilaya,
)
from apps.property.views import PropertyListView, home, property_detail


class AdminOwnershipAccessTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = RequestFactory()
        cls.wilaya = Wilaya.objects.create(id="16", name="Alger")
        cls.commune = Commune.objects.create(id="1601", name="Alger Centre", wilaya=cls.wilaya)
        cls.property_type = PropertyType.objects.create(name="Apartment", slug="apartment")

        cls.owner_one = User.objects.create_user(
            username="owner_one",
            password="password",
            is_staff=True,
        )
        cls.owner_two = User.objects.create_user(
            username="owner_two",
            password="password",
            is_staff=True,
        )
        cls.superuser = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="password",
        )

        cls.tenant_one = Tenant.objects.create(
            name="Tenant One",
            slug="tenant-one",
            domain="tenant-one.test",
            schema_name="tenant_one",
        )
        cls.tenant_two = Tenant.objects.create(
            name="Tenant Two",
            slug="tenant-two",
            domain="tenant-two.test",
            schema_name="tenant_two",
        )

        cls.agency_one = Agency.objects.create(
            tenant=cls.tenant_one,
            owner=cls.owner_one,
            name="Agency One",
            slug="agency-one",
            email="one@example.com",
            wilaya=cls.wilaya,
            commune=cls.commune,
        )
        cls.agency_two = Agency.objects.create(
            tenant=cls.tenant_two,
            owner=cls.owner_two,
            name="Agency Two",
            slug="agency-two",
            email="two@example.com",
            wilaya=cls.wilaya,
            commune=cls.commune,
        )

        cls.staff_one = User.objects.create_user(
            username="staff_one",
            password="password",
            is_staff=True,
            agency=cls.agency_one,
        )

        cls.property_one = cls.create_property(cls.agency_one, "Owned Property", is_featured=True)
        cls.property_two = cls.create_property(cls.agency_two, "Other Property", is_featured=True)

        cls.amenity_one = Amenity.objects.create(name="Elevator", icon="fas fa-elevator")
        cls.amenity_two = Amenity.objects.create(name="Parking", icon="fas fa-parking")
        PropertyAmenity.objects.create(property=cls.property_one, amenity=cls.amenity_one)
        PropertyAmenity.objects.create(property=cls.property_two, amenity=cls.amenity_two)

    @classmethod
    def create_property(cls, agency, title, **kwargs):
        return Property.objects.create(
            agency=agency,
            title=title,
            description="Test description",
            property_type=cls.property_type,
            listing_type=Property.SALE,
            price="100000.00",
            wilaya=cls.wilaya,
            commune=cls.commune,
            area_m2=80,
            **kwargs,
        )

    def request_for(self, user, path="/admin/property/property/"):
        request = self.factory.get(path)
        request.user = user
        return request

    def test_owner_only_sees_owned_agency(self):
        request = self.request_for(self.owner_one, "/admin/property/agency/")
        agency_admin = admin.site._registry[Agency]

        agency_ids = set(agency_admin.get_queryset(request).values_list("id", flat=True))

        self.assertEqual(agency_ids, {self.agency_one.id})
        self.assertTrue(agency_admin.has_change_permission(request, self.agency_one))
        self.assertFalse(agency_admin.has_change_permission(request, self.agency_two))

    def test_owner_only_sees_owned_properties(self):
        request = self.request_for(self.owner_one)
        property_admin = admin.site._registry[Property]

        property_ids = set(property_admin.get_queryset(request).values_list("id", flat=True))

        self.assertEqual(property_ids, {self.property_one.id})
        self.assertTrue(property_admin.has_change_permission(request, self.property_one))
        self.assertFalse(property_admin.has_change_permission(request, self.property_two))

    def test_agency_staff_only_sees_assigned_agency_properties(self):
        request = self.request_for(self.staff_one)
        property_admin = admin.site._registry[Property]

        property_ids = set(property_admin.get_queryset(request).values_list("id", flat=True))

        self.assertEqual(property_ids, {self.property_one.id})

    def test_non_superuser_agency_field_is_limited_to_owned_agencies(self):
        request = self.request_for(self.owner_one)
        property_admin = admin.site._registry[Property]
        agency_field = Property._meta.get_field("agency")

        form_field = property_admin.formfield_for_foreignkey(agency_field, request)
        agency_ids = set(form_field.queryset.values_list("id", flat=True))

        self.assertEqual(agency_ids, {self.agency_one.id})

    def test_non_superuser_cannot_save_property_to_other_agency(self):
        request = self.request_for(self.owner_one)
        property_admin = admin.site._registry[Property]
        property_obj = Property(
            agency=self.agency_two,
            title="Invalid Agency Property",
            description="Test description",
            property_type=self.property_type,
            listing_type=Property.SALE,
            price="100000.00",
            wilaya=self.wilaya,
            commune=self.commune,
            area_m2=80,
        )

        with self.assertRaises(PermissionDenied):
            property_admin.save_model(request, property_obj, form=None, change=False)

    def test_owner_dashboard_app_list_only_shows_agency_and_properties(self):
        request = self.request_for(self.owner_one, "/admin/")

        model_names = {
            model["object_name"]
            for app in admin.site.get_app_list(request)
            for model in app["models"]
        }

        self.assertIn("Agency", model_names)
        self.assertIn("Property", model_names)
        self.assertNotIn("Wilaya", model_names)
        self.assertNotIn("Commune", model_names)
        self.assertNotIn("PropertyType", model_names)
        self.assertNotIn("Amenity", model_names)

    def test_superuser_sees_all_agencies_and_properties(self):
        request = self.request_for(self.superuser)
        agency_admin = admin.site._registry[Agency]
        property_admin = admin.site._registry[Property]

        agency_ids = set(agency_admin.get_queryset(request).values_list("id", flat=True))
        property_ids = set(property_admin.get_queryset(request).values_list("id", flat=True))

        self.assertEqual(agency_ids, {self.agency_one.id, self.agency_two.id})
        self.assertEqual(property_ids, {self.property_one.id, self.property_two.id})

    def test_property_list_view_only_uses_current_agency_properties(self):
        request = self.request_for(self.owner_one, "/properties/")
        request.tenant = self.tenant_one
        request.agency = self.agency_one
        view = PropertyListView()
        view.setup(request)

        property_ids = set(view.get_queryset().values_list("id", flat=True))

        self.assertEqual(property_ids, {self.property_one.id})

    def test_shop_grid_route_uses_property_list_view(self):
        match = resolve("/shop-grid/")

        self.assertEqual(match.func.view_class, PropertyListView)

    def test_home_context_only_uses_current_agency_properties(self):
        request = self.request_for(self.owner_one, "/")
        request.tenant = self.tenant_one
        request.agency = self.agency_one

        with patch("apps.property.views.render") as render_mock:
            render_mock.return_value = object()
            home(request)

        context = render_mock.call_args.args[2]
        featured_ids = set(context["featured"].values_list("id", flat=True))
        amenity_ids = set(context["amenities"].values_list("id", flat=True))
        locations = list(context["locations"])

        self.assertEqual(featured_ids, {self.property_one.id})
        self.assertEqual(amenity_ids, {self.amenity_one.id})
        self.assertEqual(len(locations), 1)
        self.assertEqual(locations[0].property_count, 1)

    def test_property_detail_does_not_show_other_agency_property(self):
        request = self.request_for(self.owner_one, f"/properties/{self.property_two.reference}/")
        request.tenant = self.tenant_one
        request.agency = self.agency_one

        with self.assertRaises(Http404):
            property_detail(request, self.property_two.reference)
