import random
import uuid
from django.core.management.base import BaseCommand
from faker import Faker
from apps.property.models import (
    Agency, AgencyContact, PropertyType, Property, PropertyMedia,
    Amenity, PropertyAmenity, Wilaya, Commune
)
from apps.accounts.models import User

fake = Faker()


class Command(BaseCommand):
    help = "Populate demo data for agencies and properties"

    def handle(self, *args, **options):
        self.stdout.write("Starting demo data population...")

        # -------------------------
        # Create some PropertyTypes
        # -------------------------
        property_types = ["Apartment", "Villa", "Studio", "Shop", "Office"]
        pt_objects = []
        for pt in property_types:
            obj, _ = PropertyType.objects.get_or_create(name=pt)
            pt_objects.append(obj)
        self.stdout.write(f"Created {len(pt_objects)} property types.")

        # -------------------------
        # Create some Amenities
        # -------------------------
        amenities = ["Air Conditioning", "Heating", "Elevator", "Parking", "Pool"]
        amenity_objects = []
        for a in amenities:
            obj, _ = Amenity.objects.get_or_create(name=a)
            amenity_objects.append(obj)
        self.stdout.write(f"Created {len(amenity_objects)} amenities.")

        # -------------------------
        # Pick a random user as owner
        # -------------------------
        users = User.objects.all()
        if not users.exists():
            self.stdout.write(self.style.ERROR("No users found! Create some users first."))
            return
        owner = random.choice(users)

        # -------------------------
        # Create Agencies
        # -------------------------
        wilayas = Wilaya.objects.all()
        communes = Commune.objects.all()
        agencies = []
        for _ in range(5):
            wilaya = random.choice(wilayas)
            commune = random.choice(communes)
            agency_name = fake.company()
            agency = Agency.objects.create(
                owner=owner,
                name=agency_name,
                email=fake.email(),
                wilaya=wilaya,
                commune=commune,
                address=fake.address(),
            )
            # Add 1-3 contacts
            for _ in range(random.randint(1, 3)):
                AgencyContact.objects.create(
                    agency=agency,
                    type=random.choice([AgencyContact.PHONE, AgencyContact.WHATSAPP]),
                    number=fake.phone_number(),
                    label=random.choice(["Sales", "Rentals", "Office"]),
                    is_primary=random.choice([True, False]),
                )
            agencies.append(agency)

        self.stdout.write(f"Created {len(agencies)} agencies with contacts.")

        # -------------------------
        # Create Properties
        # -------------------------
        properties = []
        for agency in agencies:
            for _ in range(random.randint(3, 7)):
                wilaya = random.choice(wilayas)
                commune = random.choice(communes)
                property_type = random.choice(pt_objects)
                prop = Property.objects.create(
                    agency=agency,
                    title=fake.sentence(nb_words=5),
                    description=fake.text(max_nb_chars=200),
                    property_type=property_type,
                    listing_type=random.choice([Property.SALE, Property.RENT]),
                    price=random.randint(5000, 500000),
                    negotiable=random.choice([True, False]),
                    wilaya=wilaya,
                    commune=commune,
                    area_m2=random.randint(50, 500),
                    bedrooms=random.randint(1, 5),
                    bathrooms=random.randint(1, 3),
                    floor=random.randint(0, 10),
                    furnished=random.choice([True, False]),
                    parking=random.choice([True, False]),
                    status=random.choice([
                        Property.DRAFT, Property.ACTIVE, Property.SOLD, Property.RENTED
                    ]),
                )
                # Add amenities
                for _ in range(random.randint(1, len(amenity_objects))):
                    amenity = random.choice(amenity_objects)
                    PropertyAmenity.objects.get_or_create(property=prop, amenity=amenity)

                properties.append(prop)

        self.stdout.write(f"Created {len(properties)} properties with amenities.")

        self.stdout.write(self.style.SUCCESS("Demo data population completed successfully!"))
