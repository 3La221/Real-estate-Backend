import json
from django.core.management.base import BaseCommand
  # adjust import to your app name
from pathlib import Path

from apps.property.models import Commune, Wilaya

class Command(BaseCommand):
    help = "Load Wilaya and Commune data from JSON files into the database"
    # python manage.py load_wilayas_and_communes --wilaya_file="Wilaya_Of_Algeria.json" --commune_file="Commune_Of_Algeria.json"  this is how to exec the command


    def add_arguments(self, parser):
        parser.add_argument(
            "--wilaya_file",
            type=str,
            default="Wilaya_Of_Algeria.json",
            help="Path to Wilaya JSON file"
        )
        parser.add_argument(
            "--commune_file",
            type=str,
            default="Commune_Of_Algeria.json",
            help="Path to Commune JSON file"
        )

    def handle(self, *args, **options):
        wilaya_path = Path(options["wilaya_file"])
        commune_path = Path(options["commune_file"])

        if not wilaya_path.exists():
            self.stderr.write(self.style.ERROR(f"Wilaya file not found: {wilaya_path}"))
            return
        if not commune_path.exists():
            self.stderr.write(self.style.ERROR(f"Commune file not found: {commune_path}"))
            return

        # Load Wilayas
        with open(wilaya_path, "r", encoding="utf-8") as f:
            wilayas_data = json.load(f)

        # Wilaya.objects.all().delete()  # Optional: clear table first
        for w in wilayas_data:
            Wilaya.objects.create(
                id=str(w["id"]),
                name=w["name"]
            )
        self.stdout.write(self.style.SUCCESS(f"Inserted {len(wilayas_data)} wilayas."))

        # Load Communes
        with open(commune_path, "r", encoding="utf-8") as f:
            communes_data = json.load(f)

        # Commune.objects.all().delete()  # Optional: clear table first
        for c in communes_data:
            wilaya_instance = Wilaya.objects.get(id=str(c["wilaya_id"]))
            Commune.objects.create(
                id=str(c["id"]),
                name=c["name"],
                wilaya=wilaya_instance
            )
        self.stdout.write(self.style.SUCCESS(f"Inserted {len(communes_data)} communes."))
