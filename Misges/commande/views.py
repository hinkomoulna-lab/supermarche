import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from datetime import date
from django.utils import timezone
from store.models import Product, Category, Sale, SaleItem
from .models import Order, OrderItem, OrderClient


def _get_staff_name(request):
    if request.user.is_authenticated:
        return request.user.get_full_name() or request.user.username
    return 'Staff'


def _get_or_create_client(request):
    token = request.session.get('client_token')
    if token:
        try:
            return OrderClient.objects.get(token=token)
        except OrderClient.DoesNotExist:
            pass
    client = OrderClient.objects.create()
    request.session['client_token'] = client.token
    return client


def catalog(request):
    client = _get_or_create_client(request)
    categories = Category.objects.all()
    products = Product.objects.all()
    cat_id = request.GET.get('category')
    if cat_id:
        products = products.filter(category_id=cat_id)
    return render(request, 'commande/catalog.html', {
        'categories': categories,
        'products': products,
        'client': client,
    })


def add_to_cart(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    product_id = request.POST.get('product_id')
    quantity = float(request.POST.get('quantity', 1))
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Produit introuvable'}, status=404)

    cart = request.session.get('cart', {})
    key = str(product.id)
    if key in cart:
        cart[key]['quantity'] = float(cart[key]['quantity']) + quantity
    else:
        cart[key] = {
            'name': product.name,
            'price': float(product.price),
            'quantity': quantity,
            'image': product.image.url if product.image else '',
        }
    request.session['cart'] = cart
    request.session.modified = True
    return JsonResponse({'cart_count': sum(v['quantity'] for v in cart.values())})


def update_cart(request, product_id):
    cart = request.session.get('cart', {})
    key = str(product_id)
    if request.method == 'POST':
        qty = float(request.POST.get('quantity', 0))
        if qty > 0 and key in cart:
            cart[key]['quantity'] = qty
        else:
            cart.pop(key, None)
    elif request.method == 'DELETE':
        cart.pop(key, None)
    request.session['cart'] = cart
    request.session.modified = True
    return redirect('commande:cart')


def cart_view(request):
    client = _get_or_create_client(request)
    cart = request.session.get('cart', {})
    items = []
    total = 0
    for pid, data in cart.items():
        try:
            product = Product.objects.get(id=int(pid))
            stock_status = 'ok' if product.stock > 0 else 'low' if product.stock > -5 else 'out'
        except Product.DoesNotExist:
            stock_status = 'unknown'
        subtotal = data['price'] * data['quantity']
        total += subtotal
        items.append({
            'product_id': pid,
            'name': data['name'],
            'price': data['price'],
            'quantity': data['quantity'],
            'subtotal': subtotal,
            'stock_status': stock_status,
            'image': data.get('image', ''),
        })
    return render(request, 'commande/cart.html', {
        'items': items,
        'total': total,
        'client': client,
    })


@csrf_exempt
@transaction.atomic
def place_order(request):
    if request.method != 'POST':
        return redirect('commande:cart')
    client = _get_or_create_client(request)
    cart = request.session.get('cart', {})
    if not cart:
        return redirect('commande:cart')

    order = Order.objects.create(client=client)
    for pid, data in cart.items():
        product = Product.objects.filter(id=int(pid)).first()
        OrderItem.objects.create(
            order=order,
            product=product,
            product_name=data['name'],
            quantity=data['quantity'],
            unit_price=data['price'],
        )
    request.session['cart'] = {}
    request.session.modified = True
    return redirect('commande:order_detail', order_id=order.id)


def order_detail(request, order_id):
    client = _get_or_create_client(request)
    order = get_object_or_404(Order, id=order_id, client=client)
    return render(request, 'commande/order_detail.html', {'order': order})


def order_status_json(request, order_id):
    try:
        order = Order.objects.get(id=order_id)
        return JsonResponse({
            'status': order.status,
            'status_display': order.get_status_display(),
            'pickup_code': order.pickup_code if order.status == 'ready' else '',
        })
    except Order.DoesNotExist:
        return JsonResponse({'error': 'not_found'}, status=404)


def dashboard(request):
    orders = Order.objects.select_related('client').prefetch_related('items')
    status_filter = request.GET.get('status')
    if status_filter:
        orders = orders.filter(status=status_filter)

    counts = {}
    for s, label in Order.STATUS_CHOICES:
        counts[s] = Order.objects.filter(status=s).count()

    return render(request, 'commande/dashboard.html', {
        'orders': orders,
        'counts': counts,
        'current_status': status_filter or '',
    })


def create_sale_from_order(order, confirmed_by=''):
    """Create a Sale + SaleItems from a delivered Order with stock deduction."""
    if order.sale is not None:
        return order.sale

    client_name = order.client.phone or f'Client QR #{order.client.token}'

    sale = Sale.objects.create(
        sale_date=date.today(),
        sale_time=timezone.localtime().time(),
        customer_name=client_name,
        customer_phone=order.client.phone,
        notes=f'Commande QR #{order.id} — {confirmed_by}',
        amount_paid=0,
    )

    for item in order.items.filter(available=True, product__isnull=False).select_related('product'):
        SaleItem.objects.create(
            sale=sale,
            product=item.product,
            quantity=item.quantity,
            price=item.unit_price,
            sale_mode='piece',
        )
        qty = float(item.quantity)
        item.product.stock -= qty
        item.product.save(update_fields=['stock'])

    sale.update_total()
    sale.amount_paid = sale.total
    sale.sync_payment_status()
    sale.save(update_fields=['amount_paid', 'payment_status'])

    order.sale = sale
    order.save(update_fields=['sale'])

    return sale


@transaction.atomic
def update_order_status(request, order_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    order = get_object_or_404(Order, id=order_id)
    new_status = request.POST.get('status')
    valid_statuses = [s[0] for s in Order.STATUS_CHOICES]
    if new_status not in valid_statuses:
        return JsonResponse({'error': 'Statut invalide'}, status=400)
    order.status = new_status
    order.confirmed_by = _get_staff_name(request)
    order.save()

    if new_status == 'delivered':
        create_sale_from_order(order, confirmed_by=order.confirmed_by)

    return redirect('commande:dashboard')


@transaction.atomic
def convert_to_sale(request, order_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    order = get_object_or_404(Order, id=order_id)
    if order.status not in ('delivered', 'ready'):
        return JsonResponse({'error': 'Seules les commandes prêtes ou livrées peuvent être converties'}, status=400)
    confirmed_by = _get_staff_name(request)
    create_sale_from_order(order, confirmed_by=confirmed_by)
    return redirect('commande:dashboard')


def toggle_item_available(request, item_id):
    item = get_object_or_404(OrderItem, id=item_id)
    if request.method == 'POST':
        item.available = request.POST.get('available') == 'true'
        item.save()
    return redirect('commande:dashboard')
