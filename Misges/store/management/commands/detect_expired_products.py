from datetime import date

from django.core.management.base import BaseCommand

from store.models import Product, StockLoss


class Command(BaseCommand):
    help = 'Détecte les produits périmés et les convertit en pertes de stock'

    def handle(self, *args, **options):
        today = date.today()
        expired = Product.objects.filter(expiry_date__lt=today, stock__gt=0)
        count = 0

        for product in expired:
            StockLoss.objects.create(
                product=product,
                quantity=product.stock,
                loss_amount=product.stock * (product.cost_price or 0),
                reason='expired',
                notes=f'Périmé le {product.expiry_date} — détection automatique'
            )
            product.stock = 0
            product.save()
            count += 1

        self.stdout.write(self.style.SUCCESS(f'{count} produit(s) périmé(s) traité(s).'))