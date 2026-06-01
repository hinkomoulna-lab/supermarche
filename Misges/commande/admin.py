from django.contrib import admin
from .models import OrderClient, Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product_name', 'quantity', 'unit_price', 'available']


@admin.register(OrderClient)
class OrderClientAdmin(admin.ModelAdmin):
    list_display = ['token', 'phone', 'created_at']
    search_fields = ['token', 'phone']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'client', 'status', 'total', 'pickup_code', 'created_at']
    list_filter = ['status', 'created_at']
    inlines = [OrderItemInline]
    actions = ['mark_ready', 'mark_unavailable', 'mark_delivered']

    def mark_ready(self, request, qs):
        qs.update(status='ready')
    mark_ready.short_description = 'Marquer comme disponible'

    def mark_unavailable(self, request, qs):
        qs.update(status='unavailable')
    mark_unavailable.short_description = 'Marquer comme indisponible'

    def mark_delivered(self, request, qs):
        qs.update(status='delivered')
    mark_delivered.short_description = 'Marquer comme livrée'
