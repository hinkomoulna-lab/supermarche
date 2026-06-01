from decimal import Decimal
from django.contrib.auth import authenticate, login as auth_login
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status

from .models import Product, Sale, SaleItem, Category, Promotion, Customer
from .serializers import ProductSerializer, CreateSaleSerializer
from .views import _restore_stock_and_delete_sales


def _track_session(request):
    """Enregistre l'IP et le user-agent dans la session pour le suivi des appareils."""
    try:
        request.session['ip_address'] = request.META.get('REMOTE_ADDR', 'Inconnu')
        request.session['user_agent'] = request.META.get('HTTP_USER_AGENT', 'Inconnu')
        from django.utils import timezone
        request.session['last_activity'] = timezone.now().isoformat()
        request.session.set_expiry(86400 * 7)  # 7 jours
    except Exception:
        pass


@api_view(['GET'])
@permission_classes([AllowAny])
def api_product_list(request):
    _track_session(request)
    products = Product.objects.select_related('category').all()
    category = request.GET.get('category')
    q = request.GET.get('q')
    if category:
        products = products.filter(category__name__iexact=category)
    if q:
        from django.db.models import Q
        products = products.filter(
            Q(name__icontains=q) | Q(code__icontains=q) |
            Q(barcode__icontains=q) | Q(category__name__icontains=q)
        )
    serializer = ProductSerializer(products, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
def api_product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    serializer = ProductSerializer(product)
    return Response(serializer.data)


@api_view(['GET'])
def api_categories(request):
    cats = Category.objects.values('id', 'name').order_by('name')
    return Response(list(cats))


@api_view(['GET'])
def api_active_promotions(request):
    from django.utils import timezone
    today = timezone.localdate()
    promos = Promotion.objects.filter(
        is_active=True, start_date__lte=today, end_date__gte=today
    ).values('id', 'name', 'discount_type', 'discount_value')
    return Response(list(promos))


@api_view(['POST'])
@permission_classes([AllowAny])
def api_create_sale(request):
    _track_session(request)
    serializer = CreateSaleSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    items_data = data['items']
    currency = data['currency']

    crm_kw = {}
    if data.get('customer_phone'):
        crm_kw['phone'] = data['customer_phone']
        crm_kw['defaults'] = {'name': data.get('customer_name') or data['customer_phone']}
    elif data.get('customer_name'):
        crm_kw['name'] = data['customer_name']

    customer = None
    if crm_kw:
        customer, _ = Customer.objects.get_or_create(**crm_kw) if 'phone' in crm_kw else (Customer.objects.filter(**crm_kw).first(), False)

    from django.utils import timezone
    sale = Sale.objects.create(
        customer=customer,
        payment_method=data['payment_method'],
        payment_phone=data.get('payment_phone', ''),
        customer_name=data.get('customer_name', ''),
        customer_phone=data.get('customer_phone', ''),
        amount_paid=data['amount_paid'],
        notes=data.get('notes', ''),
        sale_date=timezone.localdate(),
    )

    total = Decimal('0')
    for item_data in items_data:
        product = Product.objects.get(id=item_data['product_id'])
        qty = Decimal(str(item_data['quantity']))
        if qty > product.stock:
            sale.delete()
            return Response(
                {'error': f"Stock insuffisant pour {product.name} : demandé {qty}, disponible {product.stock}."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        mode = item_data.get('sale_mode', 'piece')
        unit_price = product.sale_price_for_mode(mode)
        SaleItem.objects.create(
            sale=sale, product=product,
            quantity=qty, price=unit_price,
            sale_mode=mode,
        )
        product.stock -= qty
        product.save(update_fields=['stock'])
        total += unit_price * qty

    promotion = None
    promo_id = data.get('promotion_id')
    if promo_id:
        try:
            promotion = Promotion.objects.get(id=promo_id, is_active=True)
        except Promotion.DoesNotExist:
            pass

    if promotion:
        total = promotion.apply_discount(total)
        sale.notes = (sale.notes or '') + f' [Promo: {promotion.name}]'

    sale.total = total
    sale.sync_payment_status()
    sale.save(update_fields=['total', 'payment_status'])

    return Response({
        'id': sale.id,
        'total': str(sale.total),
        'amount_paid': str(sale.amount_paid),
        'balance_due': str(sale.balance_due),
        'payment_status': sale.payment_status,
        'url': f'/ventes/{sale.id}/',
        'invoice_url': f'/ventes/{sale.id}/facture/',
        'invoice_pdf_url': f'/ventes/{sale.id}/facture/pdf/',
        'receipt_url': f'/ventes/{sale.id}/ticket/',
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def api_login(request):
    username = request.data.get('username', '').strip()
    password = request.data.get('password', '')
    if not username or not password:
        return Response({'error': 'Identifiant et mot de passe requis'}, status=status.HTTP_400_BAD_REQUEST)
    user = authenticate(request, username=username, password=password)
    if user is None:
        return Response({'error': 'Identifiants incorrects'}, status=status.HTTP_401_UNAUTHORIZED)
    auth_login(request, user)
    return Response({
        'id': user.id,
        'username': user.username,
        'is_staff': user.is_staff,
    })


@api_view(['GET'])
def api_me(request):
    return Response({
        'id': request.user.id,
        'username': request.user.username,
        'is_staff': request.user.is_staff,
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def api_cancel_sale(request, sale_id):
    sale = get_object_or_404(Sale.objects.prefetch_related('items__product'), pk=sale_id)
    _restore_stock_and_delete_sales(Sale.objects.filter(pk=sale.pk))
    return Response({'ok': True, 'sale_id': sale_id})

@api_view(['POST'])
@permission_classes([AllowAny])
def api_reset_sales(request):
    sales = Sale.objects.prefetch_related('items__product').all()
    count = sales.count()
    _restore_stock_and_delete_sales(sales)
    return Response({'ok': True, 'deleted': count})

@api_view(['GET'])
def api_sale_history(request):
    sales = Sale.objects.select_related('customer').order_by('-created_at')[:50]
    data = [{
        'id': s.id,
        'total': str(s.total),
        'amount_paid': str(s.amount_paid),
        'balance_due': str(s.balance_due),
        'payment_status': s.payment_status,
        'payment_method': s.payment_method,
        'customer_name': s.customer_name or (s.customer.name if s.customer else ''),
        'items_count': s.items.count(),
        'created_at': s.created_at.isoformat(),
    } for s in sales]
    return Response(data)
