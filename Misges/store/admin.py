from django.contrib import admin
from .models import (
    AppFeature, CashMovement, CashSession, Category, Customer, Debt, Expense,
    InventoryAdjustment, PhoneCredit, PhoneCreditPurchase, Product, Sale,
    SaleItem, StockSupply, StoreSettings, Supplier, UserProfile,
    PurchaseOrder, PurchaseOrderItem, Promotion,
    ProductReturn, ProductReturnItem,
    CustomerOrder, CustomerOrderItem,
    SupplierReturn, SupplierReturnItem,
    BankAccount, BankTransaction,
    LoyaltyProgram, LoyaltyTransaction,
    SolarProject, SolarProjectItem, SolarComponent,
)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'address')
    search_fields = ('name', 'phone')


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'address')
    search_fields = ('name', 'phone')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'cost_price', 'stock', 'pack_size', 'carton_size', 'expiry_date')
    list_filter = ('category', 'expiry_date')
    search_fields = ('name',)

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('description', 'category', 'amount', 'date')
    list_filter = ('category', 'date')
    search_fields = ('description',)


@admin.register(StockSupply)
class StockSupplyAdmin(admin.ModelAdmin):
    list_display = ('product', 'supplier', 'quantity', 'supply_mode', 'total_units', 'unit_cost_price', 'unit_sale_price', 'date')
    list_filter = ('supplier', 'supply_mode', 'date')
    search_fields = ('product__name', 'notes')

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
    list_display = ('id', 'created_at', 'total', 'amount_paid', 'payment_status')
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


@admin.register(CashSession)
class CashSessionAdmin(admin.ModelAdmin):
    list_display = ('opened_at', 'closed_at', 'opening_balance', 'closing_balance')


@admin.register(CashMovement)
class CashMovementAdmin(admin.ModelAdmin):
    list_display = ('session', 'movement_type', 'label', 'amount', 'created_at')
    list_filter = ('movement_type',)


@admin.register(InventoryAdjustment)
class InventoryAdjustmentAdmin(admin.ModelAdmin):
    list_display = ('product', 'system_stock', 'counted_stock', 'difference', 'date')
    list_filter = ('date',)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')
    list_filter = ('role',)


class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 1


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'supplier', 'status', 'date', 'total')
    list_filter = ('status', 'date')
    inlines = [PurchaseOrderItemInline]


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ('name', 'discount_type', 'discount_value', 'start_date', 'end_date', 'active')
    list_filter = ('active', 'discount_type')
    filter_horizontal = ('products',)


class CustomerOrderItemInline(admin.TabularInline):
    model = CustomerOrderItem
    extra = 1


@admin.register(CustomerOrder)
class CustomerOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'date', 'total', 'deposit', 'status')
    list_filter = ('status', 'date')
    inlines = [CustomerOrderItemInline]


class ProductReturnItemInline(admin.TabularInline):
    model = ProductReturnItem
    extra = 1


@admin.register(ProductReturn)
class ProductReturnAdmin(admin.ModelAdmin):
    list_display = ('id', 'sale', 'date', 'reason', 'refund_amount', 'status')
    list_filter = ('reason', 'status', 'date')
    inlines = [ProductReturnItemInline]


class SupplierReturnItemInline(admin.TabularInline):
    model = SupplierReturnItem
    extra = 1


@admin.register(SupplierReturn)
class SupplierReturnAdmin(admin.ModelAdmin):
    list_display = ('id', 'supplier', 'date', 'reason', 'total', 'status')
    list_filter = ('status', 'reason', 'date')
    inlines = [SupplierReturnItemInline]


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'bank_name', 'account_number', 'balance')
    search_fields = ('name', 'account_number')


class BankTransactionInline(admin.TabularInline):
    model = BankTransaction
    extra = 0
    readonly_fields = ('created_at',)


@admin.register(BankTransaction)
class BankTransactionAdmin(admin.ModelAdmin):
    list_display = ('account', 'transaction_type', 'amount', 'date', 'description')
    list_filter = ('transaction_type', 'date')


@admin.register(LoyaltyProgram)
class LoyaltyProgramAdmin(admin.ModelAdmin):
    list_display = ('name', 'points_per_purchase', 'points_value', 'min_points_to_redeem', 'active')


@admin.register(LoyaltyTransaction)
class LoyaltyTransactionAdmin(admin.ModelAdmin):
    list_display = ('customer', 'points', 'transaction_type', 'sale', 'created_at')
    list_filter = ('transaction_type',)


class SolarProjectItemInline(admin.TabularInline):
    model = SolarProjectItem
    extra = 1


@admin.register(SolarProject)
class SolarProjectAdmin(admin.ModelAdmin):
    list_display = ('id', 'client_name', 'date', 'system_type', 'status', 'total_price', 'deposit')
    list_filter = ('status', 'system_type', 'date')
    search_fields = ('client_name', 'client_phone')
    inlines = [SolarProjectItemInline]


@admin.register(SolarComponent)
class SolarComponentAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'unit_price', 'cost_price', 'stock')
    list_filter = ('category',)
    search_fields = ('name',)

