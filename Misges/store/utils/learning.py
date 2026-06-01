from django.db.models import Count, Sum, F
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from collections import Counter

from store.models import SaleItem, Product


def _velocity(product_id, days=30):
    since = timezone.now() - timedelta(days=days)
    total = SaleItem.objects.filter(
        product_id=product_id,
        sale__created_at__gte=since
    ).aggregate(total=Sum('quantity'))['total'] or 0
    return total / days


def frequently_bought_together(product_id, limit=3, days=30):
    since = timezone.now() - timedelta(days=days)
    sale_ids = SaleItem.objects.filter(
        product_id=product_id,
        sale__created_at__gte=since
    ).values_list('sale_id', flat=True).distinct()
    return list(SaleItem.objects.filter(
        sale_id__in=sale_ids
    ).exclude(
        product_id=product_id
    ).values(
        'product_id', 'product__name', 'product__price', 'product__stock'
    ).annotate(
        frequency=Count('sale_id')
    ).order_by('-frequency')[:limit])


def top_selling(period_days=30, limit=5, exclude_ids=None):
    since = timezone.now() - timedelta(days=period_days)
    qs = SaleItem.objects.filter(sale__created_at__gte=since)
    if exclude_ids:
        qs = qs.exclude(product_id__in=exclude_ids)
    return list(qs.values(
        'product_id', 'product__name', 'product__price'
    ).annotate(
        total_qty=Sum('quantity'),
        total_revenue=Sum(F('quantity') * F('price')),
        sale_count=Count('sale_id', distinct=True)
    ).order_by('-total_qty')[:limit])


def trending(period_days=7, limit=5):
    now = timezone.now()
    recent_start = now - timedelta(days=period_days)
    past_start = now - timedelta(days=period_days * 5)
    recent = SaleItem.objects.filter(
        sale__created_at__gte=recent_start
    ).values('product_id', 'product__name').annotate(
        recent_qty=Sum('quantity')
    )
    past = SaleItem.objects.filter(
        sale__created_at__gte=past_start,
        sale__created_at__lt=recent_start
    ).values('product_id').annotate(
        past_qty=Sum('quantity')
    )
    past_map = {p['product_id']: p['past_qty'] for p in past}
    results = []
    for r in recent:
        pid = r['product_id']
        pq = past_map.get(pid, 0)
        rq = r['recent_qty']
        growth = ((rq - pq) / pq * 100) if pq > 0 else (100 if rq > 0 else 0)
        results.append({
            'product_id': pid,
            'name': r['product__name'],
            'recent_qty': rq,
            'past_qty': pq,
            'growth_pct': round(growth, 1)
        })
    results.sort(key=lambda x: x['growth_pct'], reverse=True)
    return results[:limit]


def time_based_suggestions(limit=5):
    hour = timezone.localtime().hour
    since = timezone.now() - timedelta(days=30)
    return list(SaleItem.objects.filter(
        sale__sale_time__hour__gte=hour - 2,
        sale__sale_time__hour__lte=hour + 2,
        sale__created_at__gte=since
    ).values(
        'product_id', 'product__name', 'product__price'
    ).annotate(
        frequency=Count('sale_id', distinct=True)
    ).order_by('-frequency')[:limit])


def low_stock_velocity_alerts(threshold_days=7, limit=5):
    alerts = []
    for p in Product.objects.filter(stock__gt=0):
        vel = _velocity(p.id)
        if vel > 0:
            days_left = p.stock / vel
            if days_left <= threshold_days:
                alerts.append({
                    'product_id': p.id,
                    'name': p.name,
                    'stock': p.stock,
                    'velocity': round(vel, 2),
                    'days_left': round(days_left, 1)
                })
    alerts.sort(key=lambda x: x['days_left'])
    return alerts[:limit]


def suggestions_for_cart(product_ids, limit=3):
    suggestions = Counter()
    for pid in product_ids:
        together = frequently_bought_together(pid, limit=10)
        for item in together:
            iid = item['product_id']
            if iid not in product_ids:
                suggestions[iid] += item['frequency']
    top_ids = [sid for sid, _ in suggestions.most_common(limit)]
    if not top_ids:
        return []
    prod_map = {p.id: p for p in Product.objects.filter(id__in=top_ids)}
    results = []
    for pid, freq in suggestions.most_common(limit):
        p = prod_map.get(pid)
        if p and p.stock > 0:
            results.append({
                'product_id': pid,
                'name': p.name,
                'price': p.price,
                'stock': p.stock,
                'unit': p.get_unit_display(),
                'frequency': freq,
            })
    return results
