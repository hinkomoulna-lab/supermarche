import subprocess
from types import SimpleNamespace
from datetime import date

from django.db.models import F
from django.db.utils import OperationalError, ProgrammingError

from .models import Debt, Product, StoreSettings


DEFAULT_STORE_SETTINGS = SimpleNamespace(
    store_name='Supermarché',
    logo=None,
    background_image=None,
    theme='blue',
    invoice_layout='classic',
    monthly_expense_limit=0,
)


def get_commit_count():
    try:
        return subprocess.check_output(['git', 'rev-list', '--count', 'HEAD'], stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return '0'


def store_settings(request):
    try:
        settings = StoreSettings.load()
        low_stock_products = Product.objects.filter(stock__lte=F('min_stock')).count()
        unpaid_debts = Debt.objects.filter(paid=False).count()
        overdue_debts = Debt.objects.filter(paid=False, due_date__lt=date.today()).count()
    except (OperationalError, ProgrammingError):
        settings = DEFAULT_STORE_SETTINGS
        low_stock_products = 0
        unpaid_debts = 0
        overdue_debts = 0

    alerts = []
    if low_stock_products:
        alerts.append({
            'icon': 'bi-exclamation-triangle-fill',
            'level': 'warning',
            'text': f'{low_stock_products} produit(s) en stock faible',
        })
    if unpaid_debts:
        alerts.append({
            'icon': 'bi-file-earmark-excel-fill',
            'level': 'danger' if overdue_debts else 'warning',
            'text': f'{unpaid_debts} dette(s) non remboursée(s)',
        })
    if overdue_debts:
        alerts.append({
            'icon': 'bi-alarm-fill',
            'level': 'danger',
            'text': f'{overdue_debts} dette(s) en retard',
        })

    return {
        'store_settings': settings,
        'global_alerts': alerts,
        'low_stock_count': low_stock_products,
        'commit_count': get_commit_count(),
    }
