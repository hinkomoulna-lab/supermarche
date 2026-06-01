from decimal import Decimal
from datetime import date
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.urls import reverse
from .models import CashMovement, CashSession, Category, Product, Sale, SaleItem, Expense, Debt, InventoryAdjustment, StockSupply, StoreSettings


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

    def test_product_carton_units_and_price(self):
        product = Product.objects.create(
            name='Biscuit',
            price=100,
            pack_size=10,
            pack_price=900,
            carton_size=20,
        )
        self.assertEqual(product.units_for_mode(Decimal('2'), 'carton'), Decimal('400'))
        self.assertEqual(product.sale_price_for_mode('carton'), Decimal('18000'))

    def test_price_gte_cost_price(self):
        product = Product(name='Test', price=100, cost_price=150)
        with self.assertRaises(ValidationError):
            product.clean()

    def test_clean_no_crash_when_price_none(self):
        product = Product(name='Test', cost_price=150)
        try:
            product.clean()
        except TypeError:
            self.fail('clean() crashed with TypeError when price is None')

    def test_clean_no_crash_when_cost_price_none(self):
        product = Product(name='Test', price=100)
        try:
            product.clean()
        except TypeError:
            self.fail('clean() crashed with TypeError when cost_price is None')


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

    def test_sale_balance_and_payment_status(self):
        sale = Sale.objects.create(total=Decimal('1000'), amount_paid=Decimal('400'))
        sale.sync_payment_status()
        self.assertEqual(sale.payment_status, 'partial')
        self.assertEqual(sale.balance_due, Decimal('600'))


class ExpenseModelTest(TestCase):
    def test_expense_creation(self):
        expense = Expense.objects.create(description='Loyer', amount=50000, category='loyer')
        self.assertIn('50000', str(expense))
        self.assertEqual(expense.category, 'loyer')

    def test_investment_categories_exist(self):
        choices = dict(Expense.CATEGORY_CHOICES)
        self.assertEqual(choices['amenagement_boutique'], 'Aménagement boutique')
        self.assertEqual(choices['achat_materiel'], 'Achat matériel')


class ProfitViewTest(TestCase):
    def test_profit_and_roi_context(self):
        product = Product.objects.create(name='Riz', price=100, cost_price=60, stock=20)
        sale = Sale.objects.create()
        SaleItem.objects.create(sale=sale, product=product, quantity=10, price=100)
        Expense.objects.create(description='Étagères', amount=1000, category='achat_materiel')
        Expense.objects.create(description='Loyer', amount=100, category='loyer')

        response = self.client.get(reverse('store:profit_view'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_profit'], Decimal('400'))
        self.assertEqual(response.context['operating_expenses_total'], Decimal('100'))
        self.assertEqual(response.context['initial_investment_total'], Decimal('1000'))
        self.assertEqual(response.context['net_profit'], Decimal('300'))
        self.assertEqual(response.context['roi'], Decimal('30.0'))
        self.assertEqual(response.context['investment_remaining'], Decimal('700'))
        self.assertEqual(response.context['per_product'][0]['profit_per_unit'], Decimal('40'))


class StockSupplyViewTest(TestCase):
    def test_carton_supply_updates_stock_prices_and_history(self):
        product = Product.objects.create(name='Lait', price=500, cost_price=350, stock=5, pack_size=6, carton_size=10)

        response = self.client.post(reverse('store:product_supply', args=[product.pk]), {
            'quantity': '2',
            'supply_mode': 'carton',
            'units_per_package': '12',
            'packages_per_carton': '8',
            'unit_cost_price': '300',
            'unit_sale_price': '450',
            'date': '2026-05-11',
            'notes': 'Arrivage fournisseur',
        })

        self.assertEqual(response.status_code, 302)
        product.refresh_from_db()
        self.assertEqual(product.stock, Decimal('197'))
        self.assertEqual(product.pack_size, Decimal('12'))
        self.assertEqual(product.carton_size, Decimal('8'))
        self.assertEqual(product.cost_price, Decimal('300'))
        self.assertEqual(product.price, Decimal('450'))
        supply = StockSupply.objects.get(product=product)
        self.assertEqual(supply.total_units, Decimal('192'))
        self.assertEqual(supply.total_cost, Decimal('57600'))


class CashSessionModelTest(TestCase):
    def test_expected_balance_and_gap(self):
        session = CashSession.objects.create(opening_balance=Decimal('1000'), closing_balance=Decimal('1700'))
        CashMovement.objects.create(session=session, movement_type='sale', label='Vente', amount=Decimal('900'))
        CashMovement.objects.create(session=session, movement_type='out', label='Transport', amount=Decimal('300'))
        self.assertEqual(session.expected_balance, Decimal('1600'))
        self.assertEqual(session.cash_gap, Decimal('100'))


class InventoryAdjustmentModelTest(TestCase):
    def test_inventory_difference(self):
        product = Product.objects.create(name='Huile', price=1000, stock=10)
        adjustment = InventoryAdjustment.objects.create(
            product=product,
            system_stock=product.stock,
            counted_stock=Decimal('7'),
            difference=Decimal('-3'),
        )
        self.assertEqual(adjustment.difference, Decimal('-3'))


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
        self.assertEqual(settings.theme, 'burgundy')
