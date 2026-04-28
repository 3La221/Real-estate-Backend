from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, TestCase

from apps.accounts.models import User
from apps.core.models import Tenant
from apps.property.models import Agency, Commune, Property, PropertyType, Wilaya


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

        cls.property_one = cls.create_property(cls.agency_one, "Owned Property")
        cls.property_two = cls.create_property(cls.agency_two, "Other Property")

    @classmethod
    def create_property(cls, agency, title):
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
