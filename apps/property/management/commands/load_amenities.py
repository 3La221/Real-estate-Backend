from django.core.management.base import BaseCommand
from apps.property.models import Amenity


class Command(BaseCommand):
    help = 'Load common amenities into the database'

    def handle(self, *args, **options):
        amenities = [
            'Air Conditioning',
            'Swimming Pool',
            'Central Heating',
            'Laundry Room',
            'Gym',
            'Alarm System',
            'Window Covering',
            'Internet',
            'Pets Allowed',
            'Free WiFi',
            'Car Parking',
            'Spa & Massage',
            'Elevator',
            'Security',
            'Balcony',
            'Garden',
            'Terrace',
            'Furnished',
            'Fireplace',
            'Storage Room',
        ]

        created_count = 0

        for name in amenities:
            obj, created = Amenity.objects.get_or_create(name=name)
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created amenity: {name}'))
            else:
                self.stdout.write(f'Amenity already exists: {name}')

        self.stdout.write(
            self.style.SUCCESS(f'\nTotal: {created_count} new amenities created')
        )