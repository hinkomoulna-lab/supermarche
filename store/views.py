import base64
import csv
import gzip
import hashlib
import json
import os
import socket
import uuid
import urllib.request
from urllib.parse import quote
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from io import BytesIO, StringIO
from urllib.parse import urlencode

from django.conf import settings
from django.core.management import call_command
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from django.db import transaction
from django.db.models import Sum, F, Count
from django.db.models.deletion import ProtectedError
from django.db.models.functions import TruncMonth, TruncYear
from django.core import serializers
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.http import FileResponse, HttpResponse
from django.contrib import messages
from django.utils import timezone

from .models import (
    Product, Sale, SaleItem,
    Expense, Debt,
    PhoneCredit, PhoneCreditPurchase, StoreSettings,
    AppFeature, StockLoss
)

from .forms import (
    ProductForm, SaleForm, CartAddForm,
    ExpenseForm, DebtForm,
    PhoneCreditForm, PhoneCreditPurchaseForm,
    StoreSettingsForm, AppFeatureForm,
    AccountCreationForm, AIFeatureInstructionForm,
    DataImportForm, StockLossForm
)


# =========================
# HOME
# =========================
def home(request):
    total_products = Product.objects.count()
    total_stock = Product.objects.aggregate(total=Sum('stock'))['total'] or 0
    total_sales = Sale.objects.count()

    low_stock_count = Product.objects.filter(stock__lte=F('min_stock')).count()
    recent_sales = Sale.objects.order_by('-created_at')[:5]

    total_expenses = Expense.objects.aggregate(total=Sum('amount'))['total'] or 0

    outstanding_debt_total = Debt.objects.filter(paid=False).aggregate(total=Sum('amount'))['total'] or 0
    overdue_debt_total = Debt.objects.filter(paid=False, due_date__lt=date.today()).aggregate(total=Sum('amount'))['total'] or 0
    unpaid_debt_count = Debt.objects.filter(paid=False).count()

    daily_revenue = Sale.objects.filter(sale_date=date.today()).aggregate(total=Sum('total'))['total'] or 0
    monthly_revenue = Sale.objects.filter(sale_date__year=date.today().year, sale_date__month=date.today().month).aggregate(total=Sum('total'))['total'] or 0
    yearly_revenue = Sale.objects.filter(sale_date__year=date.today().year).aggregate(total=Sum('total'))['total'] or 0
    total_revenue = Sale.objects.aggregate(total=Sum('total'))['total'] or 0

    total_phone_credits = PhoneCredit.objects.aggregate(total=Sum('amount'))['total'] or 0
    available_phone_credit_stock = PhoneCreditPurchase.get_available_stock()
    low_phone_credit_stock_alert = available_phone_credit_stock < Decimal('10000.00')

    # 7 jours
    last_7_days = []
    for i in range(6, -1, -1):
        day = date.today() - timedelta(days=i)
        total = Sale.objects.filter(sale_date=day).aggregate(total=Sum('total'))['total'] or 0
        last_7_days.append({'label': day.strftime('%d/%m'), 'value': float(total)})

    # mois
    monthly_data = {m: 0 for m in range(1, 13)}
    month_sales = Sale.objects.filter(sale_date__year=date.today().year)\
        .annotate(month=TruncMonth('sale_date'))\
        .values('month')\
        .annotate(total=Sum('total'))

    for row in month_sales:
        monthly_data[row['month'].month] = float(row['total'] or 0)

    # années
    yearly_data = {y: 0 for y in range(date.today().year - 2, date.today().year + 1)}
    year_sales = Sale.objects.filter(sale_date__year__gte=date.today().year - 2)\
        .annotate(year=TruncYear('sale_date'))\
        .values('year')\
        .annotate(total=Sum('total'))

    for row in year_sales:
        yearly_data[row['year'].year] = float(row['total'] or 0)

    return render(request, 'store/home.html', {
        'total_products': total_products,
        'total_stock': total_stock,
        'total_sales': total_sales,
        'low_stock_count': low_stock_count,
        'recent_sales': recent_sales,

        'total_expenses': float(total_expenses),
        'outstanding_debt_total': outstanding_debt_total,
        'overdue_debt_total': overdue_debt_total,
        'unpaid_debt_count': unpaid_debt_count,

        'daily_revenue': daily_revenue,
        'monthly_revenue': monthly_revenue,
        'yearly_revenue': yearly_revenue,
        'total_revenue': total_revenue,
        'total_phone_credits': total_phone_credits,
        'available_phone_credit_stock': available_phone_credit_stock,
        'low_phone_credit_stock_alert': low_phone_credit_stock_alert,

        'last_7_days_labels': json.dumps([i['label'] for i in last_7_days]),
        'last_7_days_values': json.dumps([i['value'] for i in last_7_days]),

        'month_labels': json.dumps([date(1900, m, 1).strftime('%b') for m in range(1, 13)]),
        'month_values': json.dumps([monthly_data[m] for m in range(1, 13)]),

        'year_labels': json.dumps(list(yearly_data.keys())),
        'year_values': json.dumps(list(yearly_data.values())),
    })


# =========================
# PRODUITS
# =========================
def product_list(request):
    form = CartAddForm()
    query = request.GET.get('q', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    sort = request.GET.get('sort', '')
    order = request.GET.get('order', 'asc')

    products = Product.objects.all()

    if query:
        products = products.filter(name__icontains=query)
    try:
        if min_price:
            products = products.filter(price__gte=Decimal(min_price))
        if max_price:
            products = products.filter(price__lte=Decimal(max_price))
    except InvalidOperation:
        messages.warning(request, 'Filtre de prix invalide.')

    sort_fields = {
        'name': 'name',
        'price': 'price',
        'stock': 'stock',
        'category': 'category__name',
        'expiry': 'expiry_date',
    }
    if sort in sort_fields:
        order_prefix = '-' if order == 'desc' else ''
        products = products.order_by(f'{order_prefix}{sort_fields[sort]}')

    paginator = Paginator(products, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    qp = request.GET.copy()
    if 'page' in qp:
        del qp['page']

    return render(request, 'store/product_list.html', {
        'page_obj': page_obj,
        'form': form,
        'query': query,
        'min_price': min_price,
        'max_price': max_price,
        'current_sort': sort,
        'current_order': order,
        'query_params': qp.urlencode(),
    })


def store_settings_view(request):
    settings = StoreSettings.load()
    form = StoreSettingsForm(request.POST or None, request.FILES or None, instance=settings)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Paramètres enregistrés avec succès.')
        return redirect('store:store_settings')

    return render(request, 'store/settings_form.html', {'form': form})


def mobile_access(request):
    hostnames = []
    try:
        hostname = socket.gethostname()
        for item in socket.getaddrinfo(hostname, None):
            ip = item[4][0]
            if '.' in ip and not ip.startswith('127.') and ip not in hostnames:
                hostnames.append(ip)
    except OSError:
        pass

    return render(request, 'store/mobile_access.html', {'local_ips': hostnames})


def database_tools(request):
    db_config = settings.DATABASES['default']
    db_engine = 'postgresql' if 'postgresql' in db_config.get('ENGINE', '') else 'sqlite'
    db_name = db_config.get('NAME') or db_config.get('HOST', '')
    backup_dir = os.path.join(settings.BASE_DIR, 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    backups = sorted(
        [f for f in os.listdir(backup_dir) if f.endswith('.json.gz') or f.endswith('.bak')],
        reverse=True
    )[:10]
    return render(request, 'store/database_tools.html', {
        'db_engine': db_engine,
        'db_name': db_name,
        'backups': backups,
        'backup_dir': backup_dir,
    })


def _encrypt(data, password):
    if not password:
        return data
    key = hashlib.sha256(password.encode()).digest()
    encrypted = bytearray()
    for i, b in enumerate(data):
        encrypted.append(b ^ key[i % len(key)])
    return base64.b64encode(bytes(encrypted))


def _decrypt(data, password):
    if not password:
        return data
    key = hashlib.sha256(password.encode()).digest()
    raw = base64.b64decode(data)
    decrypted = bytearray()
    for i, b in enumerate(raw):
        decrypted.append(b ^ key[i % len(key)])
    return bytes(decrypted)


def database_backup(request):
    password = request.POST.get('backup_password', '')
    buf = StringIO()
    call_command('dumpdata', 'store', indent=2, stdout=buf, exclude=['contenttypes', 'auth.permission'])
    raw = buf.getvalue().encode('utf-8')
    compressed = gzip.compress(raw)
    if password:
        compressed = _encrypt(compressed, password)
        filename = 'sauvegarde_supermarche.bak'
        content_type = 'application/octet-stream'
    else:
        filename = 'sauvegarde_supermarche.json.gz'
        content_type = 'application/gzip'
    response = HttpResponse(compressed, content_type=content_type)
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def database_export_json(request):
    response = HttpResponse(content_type='application/json')
    response['Content-Disposition'] = 'attachment; filename="donnees_supermarche.json"'
    call_command(
        'dumpdata',
        'store',
        indent=2,
        stdout=response,
        exclude=['contenttypes', 'auth.permission'],
    )
    return response


def database_import_json(request):
    form = DataImportForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        uploaded_file = request.FILES['file']
        if not uploaded_file.name.endswith('.json'):
            messages.error(request, 'Le fichier doit etre au format JSON.')
            return redirect('store:database_tools')
        try:
            content = uploaded_file.read().decode('utf-8')
            count = 0
            for obj in serializers.deserialize('json', content):
                obj.save()
                count += 1
            messages.success(request, f'{count} enregistrements importes avec succes.')
        except Exception as exc:
            messages.error(request, f'Erreur lors de l\'import : {exc}')
        return redirect('store:database_tools')
    return redirect('store:database_tools')


def feature_list(request):
    features = AppFeature.objects.all()
    counts = {
        'idea': features.filter(status='idea').count(),
        'planned': features.filter(status='planned').count(),
        'coding': features.filter(status='coding').count(),
        'done': features.filter(status='done').count(),
    }
    paginator = Paginator(features, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    qp = request.GET.copy()
    if 'page' in qp:
        del qp['page']
    return render(request, 'store/feature_list.html', {
        'page_obj': page_obj,
        'counts': counts,
        'query_params': qp.urlencode(),
    })


def feature_create(request):
    form = AppFeatureForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Fonctionnalité ajoutée avec succès.')
        return redirect('store:feature_list')
    return render(request, 'store/feature_form.html', {'form': form, 'title': 'Nouvelle fonctionnalité'})


def ai_feature_assistant(request):
    form = AIFeatureInstructionForm(request.POST or None)
    suggestion = ''

    if request.method == 'POST' and form.is_valid():
        instruction = form.cleaned_data['instruction'].strip()
        try:
            from openai import OpenAI
            client = OpenAI()
            response = client.responses.create(
                model=settings.OPENAI_MODEL,
                input=(
                    "Tu aides a modifier une application Django de gestion de magasin. "
                    "Reponds en francais avec un titre court, les fichiers a modifier, "
                    "les etapes de code, les validations a faire, et les risques. "
                    "Ne dis jamais que la modification est deja faite. Instruction: "
                    f"{instruction}"
                ),
            )
            suggestion = response.output_text
        except Exception as exc:
            suggestion = (
                "IA indisponible pour le moment. Verifie que la dependance openai est installee "
                "et que la variable OPENAI_API_KEY est configuree.\n\n"
                f"Erreur technique: {exc}"
            )

    return render(request, 'store/ai_feature_assistant.html', {'form': form, 'suggestion': suggestion})


def feature_update(request, pk):
    feature = get_object_or_404(AppFeature, pk=pk)
    form = AppFeatureForm(request.POST or None, instance=feature)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Fonctionnalité mise à jour.')
        return redirect('store:feature_list')
    return render(request, 'store/feature_form.html', {'form': form, 'title': 'Modifier la fonctionnalité'})


def feature_delete(request, pk):
    feature = get_object_or_404(AppFeature, pk=pk)
    if request.method == 'POST':
        feature.delete()
        messages.success(request, 'Fonctionnalité supprimée.')
        return redirect('store:feature_list')
    return render(request, 'store/feature_confirm_delete.html', {'feature': feature})


def modification_guide(request):
    return render(request, 'store/modification_guide.html')


def account_create(request):
    form = AccountCreationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Compte utilisateur créé avec succès.')
        return redirect('store:store_settings')
    return render(request, 'store/account_form.html', {'form': form})


def product_manage(request):
    sort = request.GET.get('sort', '')
    order = request.GET.get('order', 'asc')
    products = Product.objects.select_related('category')
    sort_fields = {
        'name': 'name',
        'category': 'category__name',
        'price': 'price',
        'cost_price': 'cost_price',
        'stock': 'stock',
        'expiry': 'expiry_date',
    }
    if sort in sort_fields:
        order_prefix = '-' if order == 'desc' else ''
        products = products.order_by(f'{order_prefix}{sort_fields[sort]}')
    else:
        products = products.order_by('name')
    paginator = Paginator(products, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    qp = request.GET.copy()
    if 'page' in qp:
        del qp['page']
    return render(request, 'store/product_manage.html', {
        'page_obj': page_obj,
        'current_sort': sort,
        'current_order': order,
        'query_params': qp.urlencode(),
    })


def download_image_from_url(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            content = response.read()
        ext = os.path.splitext(urllib.parse.urlparse(url).path)[1] or '.jpg'
        filename = f'{uuid.uuid4().hex}{ext}'
        from django.core.files.base import ContentFile
        return ContentFile(content, name=filename)
    except Exception:
        return None


def product_create(request):
    form = ProductForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        product = form.save(commit=False)
        if not request.FILES.get('image') and form.cleaned_data.get('image_url'):
            img_file = download_image_from_url(form.cleaned_data['image_url'])
            if img_file:
                product.image.save(*img_file)
        product.save()
        messages.success(request, 'Produit ajouté avec succès.')
        return redirect('store:product_manage')
    return render(request, 'store/product_form.html', {'form': form, 'title': 'Nouveau produit'})


def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    form = ProductForm(request.POST or None, request.FILES or None, instance=product)
    if request.method == 'POST' and form.is_valid():
        product = form.save(commit=False)
        if not request.FILES.get('image') and form.cleaned_data.get('image_url'):
            img_file = download_image_from_url(form.cleaned_data['image_url'])
            if img_file:
                product.image.save(*img_file)
        product.save()
        messages.success(request, 'Produit modifié avec succès.')
        return redirect('store:product_manage')
    return render(request, 'store/product_form.html', {'form': form, 'title': 'Modifier le produit'})


def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        try:
            product.delete()
            messages.success(request, 'Produit supprimé avec succès.')
        except ProtectedError:
            messages.error(
                request,
                "Ce produit a déjà été vendu. Modifie ou supprime d'abord la vente concernée."
            )
        return redirect('store:product_manage')
    return render(request, 'store/product_confirm_delete.html', {'product': product})


def create_sale(request):
    products = Product.objects.select_related('category').all()
    quick_products = (
        Product.objects.filter(name__icontains='pain')
        | Product.objects.filter(name__icontains='glace')
        | Product.objects.filter(category__name__icontains='pain')
        | Product.objects.filter(category__name__icontains='glace')
    ).distinct()[:8]

    if request.method == 'POST':
        product_ids = request.POST.getlist('product')
        quantities = request.POST.getlist('quantity')
        sale_modes = request.POST.getlist('sale_mode')
        sale_date_str = request.POST.get('sale_date', '')
        sale_notes = request.POST.get('notes', '')
        customer_name = request.POST.get('customer_name', '').strip()
        customer_phone = request.POST.get('customer_phone', '').strip()
        rows = []
        errors = []

        try:
            sale_date = date.fromisoformat(sale_date_str) if sale_date_str else date.today()
        except (ValueError, TypeError):
            sale_date = date.today()

        for index, product_id in enumerate(product_ids):
            quantity_value = quantities[index] if index < len(quantities) else ''
            mode = sale_modes[index] if index < len(sale_modes) else 'piece'
            if not product_id and not quantity_value:
                continue
            try:
                product = Product.objects.get(pk=product_id)
                quantity = Decimal(quantity_value)
                if quantity <= 0:
                    raise InvalidOperation
            except (Product.DoesNotExist, InvalidOperation, ValueError):
                errors.append('Une ligne de vente est invalide.')
                continue

            PACK_MODES = {'paquet': 1, 'carton': 12, 'cartouche': 1}
            if mode in PACK_MODES and product.pack_size > 1:
                multiplier = PACK_MODES[mode]
                effective_qty = quantity * product.pack_size * multiplier
            else:
                effective_qty = quantity
                if mode not in ('kg', 'l'):
                    mode = 'piece'

            rows.append((product, quantity, mode, effective_qty))

        if not rows:
            errors.append('Ajoute au moins un produit à la vente.')

        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            with transaction.atomic():
                sale = Sale.objects.create(
                    sale_date=sale_date, sale_time=timezone.localtime().time(),
                    notes=sale_notes, customer_name=customer_name,
                    customer_phone=customer_phone,
                )
                PACK_MODES = {'paquet': 1, 'carton': 12, 'cartouche': 1}
                for product, quantity, mode, effective_qty in rows:
                    if mode in PACK_MODES and product.pack_size > 1:
                        multiplier = PACK_MODES[mode]
                        price = (product.pack_price or (product.price * product.pack_size)) * multiplier
                    else:
                        price = product.price
                    SaleItem.objects.create(
                        sale=sale, product=product,
                        quantity=quantity, price=price,
                        sale_mode=mode
                    )
                    product.stock -= effective_qty
                    product.save(update_fields=['stock'])
                sale.update_total()
            messages.success(request, 'Vente enregistrée avec succès.')
            return redirect('store:sale_detail', sale_id=sale.id)

    return render(request, 'store/create_sale.html', {
        'products': products,
        'quick_products': quick_products,
    })


def sale_history(request):
    sort = request.GET.get('sort', '')
    order = request.GET.get('order', 'desc')

    sales = Sale.objects.prefetch_related('items')
    sort_fields = {
        'id': 'id',
        'date': 'sale_date',
        'total': 'total',
        'items': 'id',
    }
    if sort in sort_fields:
        order_prefix = '-' if order == 'desc' else ''
        sales = sales.order_by(f'{order_prefix}{sort_fields[sort]}')
    else:
        sales = sales.order_by('-created_at')

    today = date.today()
    daily_total = Sale.objects.filter(sale_date=today).aggregate(total=Sum('total'))['total'] or 0
    monthly_total = Sale.objects.filter(sale_date__year=today.year, sale_date__month=today.month).aggregate(total=Sum('total'))['total'] or 0
    total_amount = Sale.objects.aggregate(total=Sum('total'))['total'] or 0

    paginator = Paginator(sales, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    qp = request.GET.copy()
    if 'page' in qp:
        del qp['page']

    all_sales_count = Sale.objects.count()
    report_text = (
        f"Rapport des ventes - {today.strftime('%d/%m/%Y')}\n"
        f"Ventes du jour: {daily_total} FCFA\n"
        f"Ventes du mois: {monthly_total} FCFA\n"
        f"Total general: {total_amount} FCFA\n"
        f"Nombre de ventes: {all_sales_count}"
    )
    return render(request, 'store/sale_history.html', {
        'page_obj': page_obj,
        'daily_total': daily_total,
        'monthly_total': monthly_total,
        'total_amount': total_amount,
        'whatsapp_report_url': f"https://wa.me/?text={quote(report_text)}",
        'email_report_url': f"mailto:?subject={quote('Rapport des ventes')}&body={quote(report_text)}",
        'current_sort': sort,
        'current_order': order,
        'query_params': qp.urlencode(),
    })


def _restore_stock_and_delete_sales(sales):
    with transaction.atomic():
        for sale in sales.prefetch_related('items__product'):
            for item in sale.items.all():
                qty = item.quantity
                if item.sale_mode in ('paquet', 'carton', 'cartouche') and item.product.pack_size > 1:
                    mult = 12 if item.sale_mode == 'carton' else 1
                    qty = item.quantity * item.product.pack_size * mult
                item.product.stock += qty
                item.product.save(update_fields=['stock'])
            sale.delete()


def sale_detail(request, sale_id):
    sale = get_object_or_404(Sale.objects.prefetch_related('items__product'), pk=sale_id)
    return render(request, 'store/sale_detail.html', {'sale': sale})


def sale_update(request, sale_id):
    sale = get_object_or_404(Sale.objects.prefetch_related('items__product'), pk=sale_id)
    products = Product.objects.select_related('category').all()

    original_quantities = {}
    for item in sale.items.all():
        original_qtys = Decimal('0')
        if item.sale_mode in ('paquet', 'carton', 'cartouche') and item.product.pack_size > 1:
            mult = 12 if item.sale_mode == 'carton' else 1
            original_qtys = item.quantity * item.product.pack_size * mult
        else:
            original_qtys = item.quantity
        original_quantities[item.product_id] = original_quantities.get(item.product_id, Decimal('0')) + original_qtys

    if request.method == 'POST':
        product_ids = request.POST.getlist('product')
        quantities = request.POST.getlist('quantity')
        sale_modes = request.POST.getlist('sale_mode')
        sale_date_str = request.POST.get('sale_date', '')
        sale_notes = request.POST.get('notes', '')
        customer_name = request.POST.get('customer_name', '').strip()
        customer_phone = request.POST.get('customer_phone', '').strip()
        rows = []
        errors = []

        try:
            sale.sale_date = date.fromisoformat(sale_date_str) if sale_date_str else date.today()
        except (ValueError, TypeError):
            sale.sale_date = date.today()
        sale.notes = sale_notes
        sale.customer_name = customer_name
        sale.customer_phone = customer_phone

        for index, product_id in enumerate(product_ids):
            quantity_value = quantities[index] if index < len(quantities) else ''
            mode = sale_modes[index] if index < len(sale_modes) else 'piece'
            if not product_id and not quantity_value:
                continue
            try:
                product = Product.objects.get(pk=product_id)
                quantity = Decimal(quantity_value)
                if quantity <= 0:
                    raise InvalidOperation
            except (Product.DoesNotExist, InvalidOperation, ValueError):
                errors.append('Une ligne de vente est invalide.')
                continue

            if mode in ('paquet', 'carton', 'cartouche') and product.pack_size > 1:
                multiplier = 12 if mode == 'carton' else 1
                effective_qty = quantity * product.pack_size * multiplier
            else:
                effective_qty = quantity
                if mode not in ('kg', 'l'):
                    mode = 'piece'

            rows.append((product, quantity, mode, effective_qty))

        if not rows:
            errors.append('Ajoute au moins un produit à la vente.')

        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            with transaction.atomic():
                for item in sale.items.select_related('product'):
                    if item.sale_mode in ('paquet', 'carton', 'cartouche') and item.product.pack_size > 1:
                        mult = 12 if item.sale_mode == 'carton' else 1
                        item.product.stock += item.quantity * item.product.pack_size * mult
                    else:
                        item.product.stock += item.quantity
                    item.product.save(update_fields=['stock'])

                sale.items.all().delete()

                for product, quantity, mode, effective_qty in rows:
                    if mode in ('paquet', 'carton', 'cartouche') and product.pack_size > 1:
                        multiplier = 12 if mode == 'carton' else 1
                        price = (product.pack_price or (product.price * product.pack_size)) * multiplier
                    else:
                        price = product.price
                    SaleItem.objects.create(
                        sale=sale, product=product,
                        quantity=quantity, price=price,
                        sale_mode=mode
                    )
                    product.stock -= effective_qty
                    product.save(update_fields=['stock'])

                sale.save(update_fields=['sale_date', 'notes'])
                sale.update_total()

            messages.success(request, 'Vente modifiée avec succès.')
            return redirect('store:sale_detail', sale_id=sale.id)

    sale_rows = [
        {'product_id': item.product_id, 'quantity': item.quantity, 'sale_mode': item.sale_mode}
        for item in sale.items.all()
    ]
    return render(request, 'store/sale_form.html', {
        'sale': sale,
        'products': products,
        'sale_rows': sale_rows,
        'title': f'Modifier la vente #{sale.id}',
        'submit_label': 'Enregistrer les modifications',
    })


def sale_delete(request, sale_id):
    sale = get_object_or_404(Sale.objects.prefetch_related('items__product'), pk=sale_id)
    if request.method == 'POST':
        _restore_stock_and_delete_sales(Sale.objects.filter(pk=sale.pk))
        messages.success(request, 'Vente supprimée et stock restauré.')
        return redirect('store:sale_history')
    return render(request, 'store/sale_confirm_delete.html', {'sale': sale})


def sale_bulk_delete(request):
    if request.method != 'POST':
        return redirect('store:sale_history')

    action = request.POST.get('action')
    selected_ids = request.POST.getlist('sale_ids')

    if action == 'delete_all':
        sales = Sale.objects.all()
        count = sales.count()
        _restore_stock_and_delete_sales(sales)
        messages.success(request, f'{count} vente(s) supprimée(s). Stock restauré.')
    elif action == 'delete_selected':
        sales = Sale.objects.filter(id__in=selected_ids)
        count = sales.count()
        if count:
            _restore_stock_and_delete_sales(sales)
            messages.success(request, f'{count} vente(s) sélectionnée(s) supprimée(s). Stock restauré.')
        else:
            messages.warning(request, 'Sélectionne au moins une vente à supprimer.')
    else:
        messages.warning(request, 'Action de suppression invalide.')

    return redirect('store:sale_history')


def sale_invoice(request, sale_id):
    sale = get_object_or_404(Sale.objects.prefetch_related('items__product'), pk=sale_id)
    return render(request, 'store/sale_invoice.html', {'sale': sale, 'settings': StoreSettings.load()})


def sale_invoice_pdf(request, sale_id):
    from reportlab.lib import colors as rl_colors
    from reportlab.lib.units import mm
    from .utils import montant_en_lettres

    sale = get_object_or_404(Sale.objects.prefetch_related('items__product'), pk=sale_id)
    settings = StoreSettings.load()
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    margin = 45
    content_width = width - 2 * margin

    # Couleurs
    primary = rl_colors.HexColor('#2563eb')
    primary_dark = rl_colors.HexColor('#1d4ed8')
    gray_50 = rl_colors.HexColor('#f8fafc')
    gray_200 = rl_colors.HexColor('#e2e8f0')
    gray_500 = rl_colors.HexColor('#64748b')
    gray_700 = rl_colors.HexColor('#334155')

    y = height - 40

    # En-tête (bandeau coloré)
    pdf.setFillColor(primary)
    pdf.setStrokeColor(primary)
    pdf.setLineWidth(0)
    pdf.roundRect(margin - 5, y - 5, content_width + 10, 72, 8, fill=1, stroke=0)
    pdf.setFillColor(rl_colors.white)

    # Logo + nom magasin
    logo_x = margin + 8
    if settings.logo:
        try:
            pdf.drawImage(settings.logo.path, logo_x, y + 8, width=70, height=35, preserveAspectRatio=True, mask='auto')
            logo_x += 80
        except Exception:
            pass

    pdf.setFont('Helvetica-Bold', 16)
    pdf.drawString(logo_x, y + 22, settings.store_name)
    pdf.setFont('Helvetica', 8)
    store_info = settings.address or ''
    if settings.phone_number:
        store_info += f"  Tel: {settings.phone_number}" if store_info else f"Tel: {settings.phone_number}"
    if store_info:
        pdf.drawString(logo_x, y + 8, store_info)

    # N° facture à droite
    pdf.setFont('Helvetica-Bold', 22)
    pdf.drawRightString(width - margin - 8, y + 22, f'#{sale.id}')
    pdf.setFont('Helvetica', 9)
    pdf.drawRightString(width - margin - 8, y + 6, f'Date: {sale.sale_date.strftime("%d/%m/%Y")}')

    y -= 60

    # Client
    if sale.customer_name:
        pdf.setFillColor(gray_500)
        pdf.setFont('Helvetica', 7)
        pdf.drawString(margin, y, 'CLIENT')
        pdf.setFillColor(gray_700)
        pdf.setFont('Helvetica-Bold', 11)
        y -= 14
        pdf.drawString(margin, y, sale.customer_name)
        y -= 14
        if sale.customer_phone:
            pdf.setFont('Helvetica', 9)
            pdf.setFillColor(gray_500)
            pdf.drawString(margin, y, f'Tel: {sale.customer_phone}')
            y -= 18
        else:
            y -= 6

    if sale.notes:
        y -= 8
        pdf.setFillColor(rl_colors.HexColor('#9a3412'))
        pdf.setFont('Helvetica-Oblique', 9)
        pdf.drawString(margin, y, f'Note: {sale.notes}')
        y -= 18

    # Tableau en-tête
    y -= 8
    pdf.setFillColor(primary)
    pdf.roundRect(margin, y - 4, content_width, 18, 4, fill=1, stroke=0)
    pdf.setFillColor(rl_colors.white)
    pdf.setFont('Helvetica-Bold', 8)
    col_x = [margin + 8, margin + 70, margin + 270, margin + 340, margin + 390, margin + 460]
    headers = ['Code', 'Produit', 'Prix', 'Qté', 'Mode', 'Total']
    for i, h in enumerate(headers):
        pdf.drawString(col_x[i], y, h)
    y -= 26

    # Lignes du tableau
    pdf.setFont('Helvetica', 9)
    for item in sale.items.all():
        if y < 70:
            pdf.showPage()
            y = height - 40
        pdf.setFillColor(gray_700)
        pdf.drawString(col_x[0], y, item.product.code or '-')
        pdf.drawString(col_x[1], y, item.product.name[:28])
        pdf.drawRightString(col_x[2] + 50, y, f'{item.price:,.0f} F')
        pdf.drawString(col_x[3], y, f'{item.quantity:,.0f} {item.product.get_unit_display()}')
        mode_text = 'Pqt' if item.sale_mode == 'paquet' else 'Dét'
        pdf.drawString(col_x[4], y, mode_text)
        pdf.drawRightString(col_x[5] + 50, y, f'{item.subtotal:,.0f} F')
        y -= 18

    # Ligne de total
    y -= 6
    pdf.setStrokeColor(primary)
    pdf.setLineWidth(1.5)
    pdf.line(margin, y, width - margin, y)
    y -= 22
    pdf.setFillColor(primary)
    pdf.setFont('Helvetica-Bold', 14)
    pdf.drawRightString(width - margin, y, f'Total: {sale.total:,.0f} FCFA')

    # Montant en lettres
    y -= 26
    pdf.setFillColor(gray_500)
    pdf.setFont('Helvetica-Oblique', 9)
    montant_lettres = montant_en_lettres(sale.total)
    pdf.drawString(margin, y, f'Arrêtée la présente facture à la somme de : {montant_lettres}')

    # Signature
    y -= 40
    if settings.signature:
        try:
            pdf.drawImage(settings.signature.path, margin, y - 25, width=100, height=40, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass
    else:
        pdf.setFont('Helvetica', 9)
        pdf.setFillColor(gray_500)
        pdf.drawString(margin, y, 'Cachet & signature')

    pdf.setFont('Helvetica', 7)
    pdf.setFillColor(gray_500)
    pdf.drawRightString(width - margin, y, f'Facture #{sale.id} - {sale.sale_date.strftime("%d/%m/%Y")}')

    pdf.showPage()
    pdf.save()
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="facture_vente_{sale.id}.pdf"'
    return response


def export_sales_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="ventes.csv"'
    writer = csv.writer(response)
    writer.writerow(['ID', 'Date', 'Total'])
    for sale in Sale.objects.order_by('-created_at'):
        writer.writerow([sale.id, timezone.localtime(sale.created_at).strftime('%d/%m/%Y %H:%M'), sale.total])
    return response


def _get_cart(request):
    return request.session.setdefault('cart', {})


def add_to_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    form = CartAddForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        quantity = form.cleaned_data['quantity']
        cart = _get_cart(request)
        key = str(product.id)
        cart[key] = str(Decimal(cart.get(key, '0')) + quantity)
        request.session.modified = True
        messages.success(request, 'Produit ajouté au panier.')
    return redirect('store:product_list')


def remove_from_cart(request, product_id):
    cart = _get_cart(request)
    cart.pop(str(product_id), None)
    request.session.modified = True
    messages.success(request, 'Produit retiré du panier.')
    return redirect('store:cart')


def cart_view(request):
    cart = _get_cart(request)
    products = Product.objects.filter(id__in=cart.keys())
    items = []
    total = Decimal('0')

    for product in products:
        quantity = Decimal(cart.get(str(product.id), '0'))
        subtotal = product.price * quantity
        items.append({'product': product, 'quantity': quantity, 'subtotal': subtotal})
        total += subtotal

    return render(request, 'store/cart.html', {'items': items, 'total': total})


def cart_checkout(request):
    cart = _get_cart(request)
    if not cart:
        messages.warning(request, 'Le panier est vide.')
        return redirect('store:cart')

    products = {str(product.id): product for product in Product.objects.filter(id__in=cart.keys())}

    with transaction.atomic():
        sale = Sale.objects.create()
        for product_id, quantity in cart.items():
            product = products[product_id]
            quantity = Decimal(quantity)
            SaleItem.objects.create(sale=sale, product=product, quantity=quantity, price=product.price)
            product.stock -= quantity
            product.save(update_fields=['stock'])
        sale.update_total()

    request.session['cart'] = {}
    messages.success(request, 'Panier validé avec succès.')
    return redirect('store:sale_detail', sale_id=sale.id)


def expense_list(request):
    sort = request.GET.get('sort', '')
    order = request.GET.get('order', 'desc')
    expenses = Expense.objects.all()
    sort_fields = {
        'description': 'description',
        'amount': 'amount',
        'category': 'category',
        'date': 'date',
    }
    if sort in sort_fields:
        order_prefix = '-' if order == 'desc' else ''
        expenses = expenses.order_by(f'{order_prefix}{sort_fields[sort]}')
    else:
        expenses = expenses.order_by('-date')
    total_expenses = Expense.objects.aggregate(total=Sum('amount'))['total'] or 0
    settings = StoreSettings.load()
    today = date.today()

    current_month_expenses = Expense.objects.filter(date__year=today.year, date__month=today.month)
    current_month_total = current_month_expenses.aggregate(total=Sum('amount'))['total'] or 0
    monthly_limit = settings.monthly_expense_limit or 0
    over_budget = monthly_limit > 0 and current_month_total > monthly_limit
    budget_remaining = monthly_limit - current_month_total if monthly_limit else 0

    category_rows = current_month_expenses.values('category').annotate(total=Sum('amount')).order_by('-total')
    category_labels = []
    category_values = []
    category_display = dict(Expense.CATEGORY_CHOICES)
    for row in category_rows:
        category_labels.append(category_display.get(row['category'], row['category'] or 'Autre'))
        category_values.append(float(row['total'] or 0))

    monthly_totals = {m: 0 for m in range(1, 13)}
    rows = Expense.objects.filter(date__year=today.year).annotate(month=TruncMonth('date')).values('month').annotate(total=Sum('amount'))
    for row in rows:
        monthly_totals[row['month'].month] = float(row['total'] or 0)

    paginator = Paginator(expenses, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    qp = request.GET.copy()
    if 'page' in qp:
        del qp['page']

    return render(request, 'store/expense_list.html', {
        'page_obj': page_obj,
        'total_expenses': total_expenses,
        'current_month_total': current_month_total,
        'monthly_limit': monthly_limit,
        'budget_remaining': budget_remaining,
        'over_budget': over_budget,
        'category_labels': json.dumps(category_labels),
        'category_values': json.dumps(category_values),
        'month_labels': json.dumps([date(1900, m, 1).strftime('%b') for m in range(1, 13)]),
        'month_values': json.dumps([monthly_totals[m] for m in range(1, 13)]),
        'current_sort': sort,
        'current_order': order,
        'query_params': qp.urlencode(),
    })


def expense_create(request):
    form = ExpenseForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Dépense ajoutée avec succès.')
        return redirect('store:expense_list')
    return render(request, 'store/expense_form.html', {'form': form, 'title': 'Nouvelle dépense'})


def expense_update(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    form = ExpenseForm(request.POST or None, instance=expense)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Dépense modifiée avec succès.')
        return redirect('store:expense_list')
    return render(request, 'store/expense_form.html', {'form': form, 'title': 'Modifier la dépense'})


def expense_delete(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    if request.method == 'POST':
        expense.delete()
        messages.success(request, 'Dépense supprimée avec succès.')
        return redirect('store:expense_list')
    return render(request, 'store/expense_confirm_delete.html', {'expense': expense})


def debt_list(request):
    sort = request.GET.get('sort', '')
    order = request.GET.get('order', 'asc')
    debts = Debt.objects.all()
    sort_fields = {
        'person': 'person',
        'amount': 'amount',
        'due_date': 'due_date',
        'type': 'debt_type',
        'status': 'paid',
    }
    if sort in sort_fields:
        order_prefix = '-' if order == 'desc' else ''
        debts = debts.order_by(f'{order_prefix}{sort_fields[sort]}')
    else:
        debts = debts.order_by('paid', 'due_date')

    outstanding_debt_total = Debt.objects.filter(paid=False).aggregate(total=Sum('amount'))['total'] or 0
    overdue_debt_total = Debt.objects.filter(paid=False, due_date__lt=date.today()).aggregate(total=Sum('amount'))['total'] or 0

    paginator = Paginator(debts, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    qp = request.GET.copy()
    if 'page' in qp:
        del qp['page']

    return render(request, 'store/debt_list.html', {
        'page_obj': page_obj,
        'outstanding_debt_total': outstanding_debt_total,
        'overdue_debt_total': overdue_debt_total,
        'current_sort': sort,
        'current_order': order,
        'query_params': qp.urlencode(),
    })


def debt_create(request):
    form = DebtForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Dette ajoutée avec succès.')
        return redirect('store:debt_list')
    return render(request, 'store/debt_form.html', {'form': form, 'title': 'Nouvelle dette'})


def debt_update(request, pk):
    debt = get_object_or_404(Debt, pk=pk)
    form = DebtForm(request.POST or None, instance=debt)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Dette modifiée avec succès.')
        return redirect('store:debt_list')
    return render(request, 'store/debt_form.html', {'form': form, 'title': 'Modifier la dette'})


def debt_delete(request, pk):
    debt = get_object_or_404(Debt, pk=pk)
    if request.method == 'POST':
        debt.delete()
        messages.success(request, 'Dette supprimée avec succès.')
        return redirect('store:debt_list')
    return render(request, 'store/debt_confirm_delete.html', {'debt': debt})


def debt_mark_paid(request, pk):
    debt = get_object_or_404(Debt, pk=pk)
    debt.paid = True
    debt.paid_at = timezone.now()
    debt.save(update_fields=['paid', 'paid_at'])
    messages.success(request, 'Dette marquée comme réglée.')
    return redirect('store:debt_list')


def phone_credit_list(request):
    phone_credits = PhoneCredit.objects.all()
    total_phone_credits = PhoneCredit.objects.aggregate(total=Sum('amount'))['total'] or 0
    paginator = Paginator(phone_credits, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    qp = request.GET.copy()
    if 'page' in qp:
        del qp['page']
    return render(request, 'store/phone_credit_list.html', {
        'page_obj': page_obj,
        'total_phone_credits': total_phone_credits,
        'query_params': qp.urlencode(),
    })


def phone_credit_create(request):
    form = PhoneCreditForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Crédit téléphonique ajouté avec succès.')
        return redirect('store:phone_credit_list')
    return render(request, 'store/phone_credit_form.html', {'form': form, 'title': 'Nouveau crédit'})


def phone_credit_update(request, pk):
    phone_credit = get_object_or_404(PhoneCredit, pk=pk)
    form = PhoneCreditForm(request.POST or None, instance=phone_credit)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Crédit téléphonique modifié avec succès.')
        return redirect('store:phone_credit_list')
    return render(request, 'store/phone_credit_form.html', {'form': form, 'title': 'Modifier le crédit'})


def phone_credit_delete(request, pk):
    phone_credit = get_object_or_404(PhoneCredit, pk=pk)
    if request.method == 'POST':
        phone_credit.delete()
        messages.success(request, 'Crédit téléphonique supprimé avec succès.')
        return redirect('store:phone_credit_list')
    return render(request, 'store/phone_credit_confirm_delete.html', {'phone_credit': phone_credit})


def phone_credit_purchase_list(request):
    purchases = PhoneCreditPurchase.objects.all()
    total_purchased = PhoneCreditPurchase.objects.aggregate(total=Sum('amount'))['total'] or 0
    available_stock = PhoneCreditPurchase.get_available_stock()
    paginator = Paginator(purchases, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    qp = request.GET.copy()
    if 'page' in qp:
        del qp['page']
    return render(request, 'store/phone_credit_purchase_list.html', {
        'page_obj': page_obj,
        'total_purchased': total_purchased,
        'available_stock': available_stock,
        'low_stock_alert': available_stock < Decimal('10000.00'),
        'query_params': qp.urlencode(),
    })


def phone_credit_purchase_create(request):
    form = PhoneCreditPurchaseForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Achat de crédit ajouté avec succès.')
        return redirect('store:phone_credit_purchase_list')
    return render(request, 'store/phone_credit_purchase_form.html', {'form': form, 'title': 'Nouvel achat'})


def phone_credit_purchase_update(request, pk):
    purchase = get_object_or_404(PhoneCreditPurchase, pk=pk)
    form = PhoneCreditPurchaseForm(request.POST or None, instance=purchase)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Achat de crédit modifié avec succès.')
        return redirect('store:phone_credit_purchase_list')
    return render(request, 'store/phone_credit_purchase_form.html', {'form': form, 'title': 'Modifier l’achat'})


def phone_credit_purchase_delete(request, pk):
    purchase = get_object_or_404(PhoneCreditPurchase, pk=pk)
    if request.method == 'POST':
        purchase.delete()
        messages.success(request, 'Achat de crédit supprimé avec succès.')
        return redirect('store:phone_credit_purchase_list')
    return render(request, 'store/phone_credit_purchase_confirm_delete.html', {'purchase': purchase})


# =========================
# PERTES DE STOCK
# =========================
def stock_loss_list(request):
    losses = StockLoss.objects.select_related('product').all()
    total_loss = StockLoss.objects.aggregate(total=Sum('loss_amount'))['total'] or 0
    paginator = Paginator(losses, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    qp = request.GET.copy()
    if 'page' in qp:
        del qp['page']
    return render(request, 'store/stock_loss_list.html', {
        'page_obj': page_obj,
        'total_loss': total_loss,
        'query_params': qp.urlencode(),
    })


def stock_loss_create(request):
    form = StockLossForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        loss = form.save()
        product = loss.product
        if product.stock >= loss.quantity:
            product.stock -= loss.quantity
            product.save()
        messages.success(request, 'Perte enregistrée avec succès.')
        return redirect('store:stock_loss_list')
    return render(request, 'store/stock_loss_form.html', {
        'form': form,
        'title': 'Nouvelle perte',
    })


def stock_loss_expired(request):
    today = date.today()
    expired_products = Product.objects.filter(
        expiry_date__lt=today,
        stock__gt=0
    ).order_by('expiry_date')

    if request.method == 'POST':
        product_ids = request.POST.getlist('products')
        for pid in product_ids:
            product = get_object_or_404(Product, pk=pid)
            if product.stock > 0:
                StockLoss.objects.create(
                    product=product,
                    quantity=product.stock,
                    loss_amount=product.stock * (product.cost_price or 0),
                    reason='expired',
                    notes=f'Périmé le {product.expiry_date}'
                )
                product.stock = 0
                product.save()
        messages.success(request, f'{len(product_ids)} produit(s) périmé(s) marqué(s) comme perte.')
        return redirect('store:stock_loss_list')

    return render(request, 'store/stock_loss_expired.html', {
        'expired_products': expired_products,
        'today': today,
    })


# =========================
# BÉNÉFICES
# =========================
def profit_view(request):
    items = SaleItem.objects.select_related('product').all()
    per_product = {}
    total_revenue = Decimal('0')
    total_cost = Decimal('0')

    PACK_MODES = {'paquet': 1, 'carton': 12, 'cartouche': 1}

    for item in items:
        revenue = item.subtotal
        if item.sale_mode in PACK_MODES and item.product.pack_size > 1:
            mult = PACK_MODES[item.sale_mode]
            effective_qty = item.quantity * item.product.pack_size * mult
        else:
            effective_qty = item.quantity
        cost = effective_qty * (item.product.cost_price or 0)
        profit = revenue - cost

        total_revenue += revenue
        total_cost += cost

        pid = item.product_id
        if pid not in per_product:
            per_product[pid] = {
                'product': item.product,
                'qty': Decimal('0'),
                'revenue': Decimal('0'),
                'cost': Decimal('0'),
                'profit': Decimal('0'),
            }
        per_product[pid]['qty'] += effective_qty
        per_product[pid]['revenue'] += revenue
        per_product[pid]['cost'] += cost
        per_product[pid]['profit'] += profit

    for p in per_product.values():
        p['margin'] = (p['profit'] / p['revenue'] * 100) if p['revenue'] else 0

    total_profit = total_revenue - total_cost
    margin = (total_profit / total_revenue * 100) if total_revenue else 0

    return render(request, 'store/profit_list.html', {
        'per_product': sorted(per_product.values(), key=lambda x: -x['profit']),
        'total_revenue': total_revenue,
        'total_cost': total_cost,
        'total_profit': total_profit,
        'margin': margin,
    })
