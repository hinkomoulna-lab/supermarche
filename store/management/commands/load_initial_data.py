from django.core.management import call_command
from django.core.management.base import BaseCommand
from store.models import Product


class Command(BaseCommand):
    help = "Charge les données initiales (full_data.json, puis data.json en fallback)"

    def handle(self, *args, **options):
        if Product.objects.count() > 0:
            self.stdout.write("Des produits existent déjà, import ignoré")
            return

        try:
            call_command('sync_data', '--force')
        except Exception as e:
            self.stdout.write(f"Sync data indisponible ({e}), fallback sur data.json...")
            call_command("loaddata", "data.json", "--ignorenonexistent")

        self.stdout.write(self.style.SUCCESS("Données initiales importées"))
