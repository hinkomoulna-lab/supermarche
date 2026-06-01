from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db.models import Sum

from store.models import Debt, Expense, Product, Sale, StoreSettings
from store.notifications import send_sms


def build_report_text() -> str:
    today = date.today()
    daily_revenue = Sale.objects.filter(sale_date=today).aggregate(total=Sum('total'))['total'] or Decimal('0')
    monthly_revenue = Sale.objects.filter(
        sale_date__year=today.year, sale_date__month=today.month
    ).aggregate(total=Sum('total'))['total'] or Decimal('0')
    daily_expenses = Expense.objects.filter(date=today).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    sale_count = Sale.objects.filter(sale_date=today).count()
    overdue_debts = Debt.objects.filter(paid=False, due_date__lt=today).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    low_stock = Product.objects.filter(stock__lte=0).count()
    settings = StoreSettings.load()

    lines = [
        f'Rapport {settings.store_name}',
        f'{today.strftime("%d/%m/%Y")}',
        '',
        f'Ventes du jour: {daily_revenue:,.0f} FCFA'.replace(',', ' '),
        f'Ventes du mois: {monthly_revenue:,.0f} FCFA'.replace(',', ' '),
        f'Nombre de ventes: {sale_count}',
        f'Dépenses du jour: {daily_expenses:,.0f} FCFA'.replace(',', ' '),
        f'Dettes impayées: {overdue_debts:,.0f} FCFA'.replace(',', ' '),
        f'Produits en rupture: {low_stock}',
    ]
    return '\n'.join(lines)


class Command(BaseCommand):
    help = 'Envoie le rapport quotidien par SMS'

    def handle(self, *args, **options):
        settings = StoreSettings.load()
        phone = settings.phone_number
        if not phone:
            self.stdout.write(self.style.WARNING('Aucun numéro de téléphone configuré dans les paramètres.'))
            return
        report = build_report_text()
        ok = send_sms(phone, report)
        if ok:
            self.stdout.write(self.style.SUCCESS('Rapport quotidien envoyé par SMS.'))
        else:
            self.stdout.write(self.style.ERROR("Échec de l'envoi du SMS."))
