from django.core.management.base import BaseCommand
from apps.property.models import PropertyType


class Command(BaseCommand):
    help = 'Load common property types into the database'

    def handle(self, *args, **options):
        property_types = [
            'Apartment',
            'Villa',
            'House',
            'Studio',
            'Duplex',
            'Penthouse',
            'Commercial',
            'Office',
            'Land',
            'Garage',
            'Farm',
            'Building',
        ]

        created_count = 0
        for type_name in property_types:
            obj, created = PropertyType.objects.get_or_create(name=type_name)
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created property type: {type_name}'))
            else:
                self.stdout.write(f'Property type already exists: {type_name}')

        self.stdout.write(self.style.SUCCESS(f'\nTotal: {created_count} new property types created'))
