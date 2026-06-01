import subprocess
from types import SimpleNamespace
from datetime import date, timedelta

from django.db.models import F
from django.db.utils import OperationalError, ProgrammingError

from .models import Debt, Product, StoreSettings


DEFAULT_STORE_SETTINGS = SimpleNamespace(
    store_name='Supermarché',
    logo=None,
    background_image=None,
    theme='burgundy',
    scripture_mode='bible',
    invoice_layout='classic',
    monthly_expense_limit=0,
    currency='XOF',
    label_layout='compact',
    label_font_size='medium',
    label_border_style='dashed',
    label_columns_screen=2,
    label_columns_print=4,
    label_logo=None,
    label_show_store_name=True,
    label_show_barcode=True,
    label_show_code=False,
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
        expiring_soon = Product.objects.filter(
            expiry_date__gte=date.today(),
            expiry_date__lte=date.today() + timedelta(days=7)
        ).count()
        expired = Product.objects.filter(expiry_date__lt=date.today()).count()
    except (OperationalError, ProgrammingError):
        settings = DEFAULT_STORE_SETTINGS
        low_stock_products = 0
        unpaid_debts = 0
        overdue_debts = 0
        expiring_soon = 0
        expired = 0

    alerts = []
    if low_stock_products:
        alerts.append({
            'icon': 'bi-exclamation-triangle-fill',
            'level': 'warning',
            'text': f'{low_stock_products} produit(s) en stock faible',
        })
    if expired:
        alerts.append({
            'icon': 'bi-x-octagon-fill',
            'level': 'danger',
            'text': f'{expired} produit(s) périmé(s) en stock',
        })
    if expiring_soon:
        alerts.append({
            'icon': 'bi-clock-fill',
            'level': 'warning',
            'text': f'{expiring_soon} produit(s) expirent dans < 7 jours',
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

    CURRENCY_SYMBOLS = {'XOF': 'FCFA', 'EUR': '€', 'USD': '$'}
    cart = request.session.get('cart', {})
    cart_count = sum(max(int(v or 0), 0) for v in cart.values())
    return {
        'store_settings': settings,
        'global_alerts': alerts,
        'low_stock_count': low_stock_products,
        'commit_count': get_commit_count(),
        'currency_symbol': CURRENCY_SYMBOLS.get(settings.currency, 'FCFA'),
        'cart_count': cart_count,
    }
