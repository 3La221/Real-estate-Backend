from django.core.management.base import BaseCommand
from django.utils.text import slugify
from apps.core.models import Tenant


class Command(BaseCommand):
    help = 'Create a new tenant for multi-tenancy'

    def add_arguments(self, parser):
        parser.add_argument('name', type=str, help='Tenant name')
        parser.add_argument('domain', type=str, help='Primary domain (e.g., example.com)')
        parser.add_argument(
            '--slug',
            type=str,
            help='Tenant slug (auto-generated from name if not provided)'
        )
        parser.add_argument(
            '--additional-domains',
            nargs='+',
            help='Additional domains for this tenant'
        )
        parser.add_argument(
            '--inactive',
            action='store_true',
            help='Create tenant as inactive'
        )

    def handle(self, *args, **options):
        name = options['name']
        domain = options['domain'].lower()
        slug = options.get('slug') or slugify(name)
        additional_domains = options.get('additional_domains', [])
        is_active = not options.get('inactive', False)

        if Tenant.objects.filter(domain=domain).exists():
            self.stdout.write(
                self.style.ERROR(f'Tenant with domain "{domain}" already exists!')
            )
            return

        tenant = Tenant.objects.create(
            name=name,
            slug=slug,
            domain=domain,
            additional_domains=additional_domains,
            is_active=is_active
        )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created tenant: {tenant.name}')
        )
        self.stdout.write(f'  ID: {tenant.id}')
        self.stdout.write(f'  Slug: {tenant.slug}')
        self.stdout.write(f'  Domain: {tenant.domain}')
        if additional_domains:
            self.stdout.write(f'  Additional domains: {", ".join(additional_domains)}')
        self.stdout.write(f'  Active: {tenant.is_active}')
