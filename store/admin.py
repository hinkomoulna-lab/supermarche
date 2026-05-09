from django.contrib import admin
from .models import AppFeature, Category, Debt, Expense, PhoneCredit, PhoneCreditPurchase, Product, Sale, SaleItem, StoreSettings

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'cost_price', 'stock', 'expiry_date')
    list_filter = ('category', 'expiry_date')
    search_fields = ('name',)

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('description', 'category', 'amount', 'date')
    list_filter = ('category', 'date')
    search_fields = ('description',)

@admin.register(Debt)
class DebtAdmin(admin.ModelAdmin):
    list_display = ('person', 'debt_type', 'amount', 'due_date', 'paid')
    list_filter = ('debt_type', 'paid')
    search_fields = ('person',)

@admin.register(PhoneCredit)
class PhoneCreditAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'operator', 'amount', 'credit_amount', 'date')
    list_filter = ('operator', 'date')
    search_fields = ('phone_number',)

@admin.register(PhoneCreditPurchase)
class PhoneCreditPurchaseAdmin(admin.ModelAdmin):
    list_display = ('amount', 'date')
    list_filter = ('date',)

class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    readonly_fields = ('subtotal',)

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at', 'total')
    readonly_fields = ('total',)
    inlines = [SaleItemInline]

@admin.register(SaleItem)
class SaleItemAdmin(admin.ModelAdmin):
    list_display = ('sale', 'product', 'quantity', 'price', 'subtotal')
    raw_id_fields = ('product',)


@admin.register(StoreSettings)
class StoreSettingsAdmin(admin.ModelAdmin):
    list_display = ('store_name', 'theme', 'invoice_layout')


@admin.register(AppFeature)
class AppFeatureAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'updated_at')
    list_filter = ('status',)
    search_fields = ('title', 'description', 'code_notes')

