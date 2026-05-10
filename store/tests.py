from decimal import Decimal
from datetime import date
from django.test import TestCase
from django.core.exceptions import ValidationError
from .models import Category, Product, Sale, SaleItem, Expense, Debt, StoreSettings


class CategoryModelTest(TestCase):
    def test_category_creation(self):
        category = Category.objects.create(name='Boisson')
        self.assertEqual(str(category), 'Boisson')


class ProductModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Alimentation')

    def test_product_auto_code(self):
        product = Product.objects.create(name='Riz', price=500, stock=10)
        self.assertTrue(product.code.startswith('ART-'))

    def test_product_available_property(self):
        product = Product.objects.create(name='Sel', price=100, stock=5)
        self.assertTrue(product.is_available)
        product.stock = 0
        self.assertFalse(product.is_available)

    def test_product_needs_restock(self):
        product = Product.objects.create(name='Sucre', price=300, stock=2, min_stock=5)
        self.assertTrue(product.needs_restock)
        product.stock = 10
        self.assertFalse(product.needs_restock)

    def test_price_gte_cost_price(self):
        product = Product(name='Test', price=100, cost_price=150)
        with self.assertRaises(ValidationError):
            product.clean()


class SaleModelTest(TestCase):
    def setUp(self):
        self.product = Product.objects.create(name='Pain', price=250, stock=20)

    def test_sale_creation(self):
        sale = Sale.objects.create()
        SaleItem.objects.create(sale=sale, product=self.product, quantity=2, price=250)
        sale.update_total()
        self.assertEqual(sale.total, Decimal('500'))
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 20)

    def test_sale_calculate_total(self):
        sale = Sale.objects.create()
        SaleItem.objects.create(sale=sale, product=self.product, quantity=3, price=250)
        SaleItem.objects.create(sale=sale, product=self.product, quantity=1, price=250)
        self.assertEqual(sale.calculate_total(), Decimal('1000'))

    def test_sale_date_default(self):
        sale = Sale.objects.create()
        self.assertEqual(sale.sale_date, date.today())


class ExpenseModelTest(TestCase):
    def test_expense_creation(self):
        expense = Expense.objects.create(description='Loyer', amount=50000, category='loyer')
        self.assertIn('50000', str(expense))
        self.assertEqual(expense.category, 'loyer')


class DebtModelTest(TestCase):
    def test_debt_status_pending(self):
        debt = Debt.objects.create(
            debt_type='payable', person='Jean',
            amount=10000, due_date=date(2099, 12, 31)
        )
        self.assertEqual(debt.status, 'En attente')

    def test_debt_status_overdue(self):
        debt = Debt.objects.create(
            debt_type='payable', person='Paul',
            amount=5000, due_date=date(2020, 1, 1)
        )
        self.assertEqual(debt.status, 'En retard')

    def test_debt_status_paid(self):
        debt = Debt.objects.create(
            debt_type='payable', person='Marie',
            amount=3000, due_date=date(2020, 1, 1), paid=True
        )
        self.assertEqual(debt.status, 'Réglée')


class StoreSettingsModelTest(TestCase):
    def test_load_returns_singleton(self):
        settings1 = StoreSettings.load()
        settings2 = StoreSettings.load()
        self.assertEqual(settings1.pk, settings2.pk)
        self.assertEqual(settings1.store_name, 'Supermarché')

    def test_default_theme(self):
        settings = StoreSettings.load()
        self.assertEqual(settings.theme, 'blue')
