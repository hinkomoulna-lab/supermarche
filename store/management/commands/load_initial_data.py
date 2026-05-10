from django.core.management import call_command
from django.core.management.base import BaseCommand
from store.models import Product


class Command(BaseCommand):
    help = "Charge les données initiales si la base est vide"

    def handle(self, *args, **options):
        if Product.objects.count() > 0:
            self.stdout.write("Des produits existent déjà, import ignoré")
            return
        call_command("loaddata", "data.json", "--ignorenonexistent")
        self.stdout.write(self.style.SUCCESS("Données initiales importées"))
