from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from store.models import Product, Sale, StockSupply


class Command(BaseCommand):
    help = "Audite les données critiques et corrige les incohérences simples avec --fix."

    def add_arguments(self, parser):
        parser.add_argument(
            "--fix",
            action="store_true",
            help="Corrige les problèmes non destructifs détectés.",
        )

    def handle(self, *args, **options):
        fix = options["fix"]
        issues = []
        fixed = 0

        with transaction.atomic():
            for product in Product.objects.select_for_update().all():
                changed = []

                if not product.code:
                    product.save()
                    fixed += 1
                    continue

                if product.barcode == "":
                    issues.append(f"Produit #{product.pk}: code-barres vide")
                    if fix:
                        product.barcode = None
                        changed.append("barcode")

                for field in ("price", "cost_price", "stock", "min_stock", "pack_size", "carton_size"):
                    value = getattr(product, field)
                    if value is not None and value < 0:
                        issues.append(f"Produit {product.code}: {field} negatif ({value})")
                        if fix:
                            setattr(product, field, Decimal("0"))
                            changed.append(field)

                if product.pack_size is not None and product.pack_size < 1:
                    issues.append(f"Produit {product.code}: taille paquet invalide ({product.pack_size})")
                    if fix:
                        product.pack_size = Decimal("1")
                        changed.append("pack_size")

                if product.carton_size is not None and product.carton_size < 1:
                    issues.append(f"Produit {product.code}: carton invalide ({product.carton_size})")
                    if fix:
                        product.carton_size = Decimal("1")
                        changed.append("carton_size")

                if changed:
                    product.save(update_fields=sorted(set(changed)))
                    fixed += 1

            for sale in Sale.objects.select_for_update().prefetch_related("items"):
                expected_total = sum(item.subtotal for item in sale.items.all())
                changed = []

                if sale.total != expected_total:
                    issues.append(f"Vente #{sale.pk}: total {sale.total} != lignes {expected_total}")
                    if fix:
                        sale.total = expected_total
                        changed.append("total")

                if sale.amount_paid < 0:
                    issues.append(f"Vente #{sale.pk}: montant paye negatif ({sale.amount_paid})")
                    if fix:
                        sale.amount_paid = Decimal("0")
                        changed.append("amount_paid")

                old_status = sale.payment_status
                sale.sync_payment_status()
                if sale.payment_status != old_status:
                    issues.append(f"Vente #{sale.pk}: statut paiement incoherent ({old_status})")
                    if fix:
                        changed.append("payment_status")
                    else:
                        sale.payment_status = old_status

                if changed:
                    sale.save(update_fields=sorted(set(changed)))
                    fixed += 1

            for supply in StockSupply.objects.select_for_update().select_related("product"):
                changed = []
                if supply.quantity < 0:
                    issues.append(f"Approvisionnement #{supply.pk}: quantite negative")
                    if fix:
                        supply.quantity = Decimal("0")
                        changed.append("quantity")
                if supply.units_per_package < 1:
                    issues.append(f"Approvisionnement #{supply.pk}: unites par paquet invalides")
                    if fix:
                        supply.units_per_package = Decimal("1")
                        changed.append("units_per_package")
                if supply.packages_per_carton < 1:
                    issues.append(f"Approvisionnement #{supply.pk}: paquets par carton invalides")
                    if fix:
                        supply.packages_per_carton = Decimal("1")
                        changed.append("packages_per_carton")

                if changed:
                    supply.save(update_fields=sorted(set(changed)))
                    fixed += 1

        if issues:
            self.stdout.write(self.style.WARNING(f"{len(issues)} probleme(s) detecte(s)."))
            for issue in issues[:50]:
                self.stdout.write(f"- {issue}")
            if len(issues) > 50:
                self.stdout.write(f"... {len(issues) - 50} autre(s) probleme(s)")
        else:
            self.stdout.write(self.style.SUCCESS("Aucun probleme critique detecte."))

        if fix:
            self.stdout.write(self.style.SUCCESS(f"{fixed} objet(s) corrige(s)."))
