from rest_framework import serializers
from .models import Product, Sale, SaleItem, Category, Promotion

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']

class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    unit_display = serializers.CharField(source='get_unit_display', read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'code', 'barcode', 'price', 'price_eur', 'price_usd',
            'stock', 'unit', 'unit_display', 'category', 'category_name',
            'min_stock', 'is_available', 'image',
        ]

class SaleItemSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.DecimalField(max_digits=10, decimal_places=2)
    sale_mode = serializers.CharField(default='piece')

class CreateSaleSerializer(serializers.Serializer):
    items = SaleItemSerializer(many=True)
    amount_paid = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_method = serializers.ChoiceField(
        choices=['cash', 'orange_money', 'malitel_momo', 'mixte'],
        default='cash'
    )
    payment_phone = serializers.CharField(required=False, allow_blank=True, default='')
    customer_name = serializers.CharField(required=False, allow_blank=True, default='')
    customer_phone = serializers.CharField(required=False, allow_blank=True, default='')
    currency = serializers.ChoiceField(choices=['XOF', 'EUR', 'USD'], default='XOF')
    notes = serializers.CharField(required=False, allow_blank=True, default='')
    promotion_id = serializers.IntegerField(required=False, allow_null=True, default=None)
    giftcard_code = serializers.CharField(required=False, allow_blank=True, default='')

    def validate_items(self, items):
        if not items:
            raise serializers.ValidationError("Au moins un produit est requis")
        errors = []
        for i, item in enumerate(items):
            try:
                Product.objects.get(id=item['product_id'])
            except Product.DoesNotExist:
                errors.append(f"Produit ID {item['product_id']} introuvable à la ligne {i+1}")
            if item['quantity'] <= 0:
                errors.append(f"Quantité invalide à la ligne {i+1}")
        if errors:
            raise serializers.ValidationError(errors)
        return items
