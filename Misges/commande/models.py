import uuid, secrets
from decimal import Decimal
from django.db import models
from django.db.models import Sum
from django.utils import timezone
from store.models import Product


def generate_client_token():
    return secrets.token_hex(4).upper()


def generate_pickup_code():
    return str(secrets.randbelow(9000) + 1000)


class OrderClient(models.Model):
    token = models.CharField(max_length=8, unique=True, default=generate_client_token)
    phone = models.CharField('Téléphone', max_length=30, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Client {self.token}'


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', '🟡 En attente'),
        ('preparing', '🔵 En préparation'),
        ('ready', '✅ Disponible'),
        ('unavailable', '❌ Indisponible'),
        ('delivered', '🎉 Livrée'),
        ('cancelled', '✖️ Annulée'),
    ]

    client = models.ForeignKey(OrderClient, related_name='orders', on_delete=models.CASCADE)
    token = models.CharField(max_length=8, default=generate_client_token)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    pickup_code = models.CharField('Code retrait', max_length=4, default=generate_pickup_code)
    notes = models.TextField('Notes', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_by = models.CharField('Confirmé par', max_length=100, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Commande #{self.id} ({self.client.token})'

    @property
    def total(self):
        return self.items.aggregate(t=Sum(models.F('quantity') * models.F('unit_price')))['t'] or Decimal('0')

    @property
    def item_count(self):
        return self.items.count()


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField('Produit', max_length=200)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    available = models.BooleanField('Disponible', default=True)

    def __str__(self):
        return f'{self.quantity} x {self.product_name}'

    @property
    def subtotal(self):
        return self.quantity * self.unit_price
