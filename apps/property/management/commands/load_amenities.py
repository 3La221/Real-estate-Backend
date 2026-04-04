from django.core.management.base import BaseCommand
from apps.property.models import Amenity

class Command(BaseCommand):
    help = "Seed default amenities for Algerian market (French)"

    def handle(self, *args, **kwargs):
        amenities = [
            {"name": "Résidentiel", "icon": "fas fa-laptop-house"},
            {"name": "Parking", "icon": "fas fa-car-side"},
            {"name": "Commercial", "icon": "far fa-object-group"},
            {"name": "Appartement", "icon": "fas fa-building"},
            {"name": "Industriel", "icon": "fas fa-industry"},
            {"name": "Code de construction", "icon": "fas fa-house-damage"},
            {"name": "Piscine", "icon": "fas fa-swimmer"},
            {"name": "Sécurité privée", "icon": "fas fa-shield-alt"},
            {"name": "Maison intelligente", "icon": "fas fa-home"},
            {"name": "Jardin", "icon": "fas fa-leaf"},
            {"name": "Climatisation", "icon": "fas fa-snowflake"},
            {"name": "Ascenseur", "icon": "fas fa-elevator"},
        ]

        created_count = 0
        existing_count = 0

        for amenity in amenities:
            obj, created = Amenity.objects.get_or_create(
                name=amenity["name"],
                defaults={"icon": amenity["icon"]}
            )

            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"✔ Created: {obj.name}"))
            else:
                existing_count += 1
                self.stdout.write(self.style.WARNING(f"⚠ Already exists: {obj.name}"))

        self.stdout.write(self.style.SUCCESS(
            f"\nDone: {created_count} created, {existing_count} already existed."
        ))