from datetime import date
from decimal import Decimal

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import (
    CashMovement, CashSession, Category, Customer, Debt, Expense,
    InventoryAdjustment,
    PhoneCredit, PhoneCreditPurchase,
    Product, StoreSettings, AppFeature, Supplier,
    StockLoss, StockSupply, UserProfile,
    PurchaseOrder, PurchaseOrderItem, Promotion,
    ProductReturn, ProductReturnItem,
    CustomerOrder, CustomerOrderItem,
    SupplierReturn, SupplierReturnItem,
    BankAccount, BankTransaction,
    LoyaltyProgram, LoyaltyTransaction,
    SolarProject, SolarProjectItem, SolarComponent,
    Employee,
)

# ======================
# VENTE SIMPLE
# ======================
class SaleForm(forms.Form):
    product = forms.ModelChoiceField(
        queryset=Product.objects.filter(stock__gt=0),
        label='Produit',
        empty_label='Choisir un produit',
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )

    quantity = forms.DecimalField(
        min_value=0.01,
        max_digits=10,
        decimal_places=2,
        label='Quantité',
        widget=forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01'})
    )


class AIFeatureInstructionForm(forms.Form):
    instruction = forms.CharField(
        label='Instruction pour l’IA',
        widget=forms.Textarea(attrs={
            'class': 'form-control form-control-sm',
            'rows': 4,
            'placeholder': 'Ex: ajoute une remise automatique pour les ventes de pain et de glaces...',
            'data-voice': 'true'
        })
    )


# ======================
# PANIER
# ======================
class CartAddForm(forms.Form):
    quantity = forms.DecimalField(
        min_value=0.01,
        max_digits=10,
        decimal_places=2,
        initial=1,
        label='Quantité à ajouter',
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-sm',
            'step': '0.01',
            'style': 'width:90px;'
        })
    )


# ======================
# PRODUITS
# ======================
class ProductForm(forms.ModelForm):
    new_category = forms.CharField(
        required=False,
        label='Ou crée une nouvelle catégorie',
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'Ex: Alimentation, Boisson, Hygiène...',
            'data-voice': 'true'
        })
    )

    image_url = forms.URLField(
        required=False,
        label='Ou colle une URL d\'image (Google)',
        widget=forms.URLInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'Copie l\'URL d\'une image depuis Google Images...'
        })
    )

    class Meta:
        model = Product
        fields = [
            'code', 'barcode', 'name', 'image',
            'category',
            'unit', 'price', 'cost_price',
            'stock', 'min_stock', 'expiry_date',
            'pack_size', 'pack_price', 'carton_size',
            'price_eur', 'price_usd',
        ]

        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Automatique si vide',
                'data-voice': 'true'
            }),
            'barcode': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Scanner ou saisir le code-barres'}),
            'name': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'data-voice': 'true'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control form-control-sm', 'accept': 'image/*'}),
            'category': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'unit': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'price': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'cost_price': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'min_stock': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control form-control-sm', 'type': 'date'}),
            'pack_size': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Ex: 12 pièces par paquet'}),
            'pack_price': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Laissez vide = prix unitaire × taille'}),
            'carton_size': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Ex: 24 paquets par carton'}),
            'price_eur': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01', 'min': '0'}),
            'price_usd': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01', 'min': '0'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ('unit', 'cost_price', 'stock', 'min_stock', 'pack_size', 'carton_size'):
            self.fields[field].required = False

    MARGIN_RATE = Decimal('1.10')

    def clean(self):
        cleaned_data = super().clean()

        price = cleaned_data.get('price')
        cost_price = cleaned_data.get('cost_price')
        new_category = cleaned_data.get('new_category')

        if not price and cost_price:
            price = (cost_price * self.MARGIN_RATE).quantize(Decimal('0.01'))
            cleaned_data['price'] = price

        if price and cost_price and price < cost_price:
            self.add_error('price', "Le prix de vente doit être supérieur ou égal au prix d'achat.")

        if new_category:
            cleaned_data['new_category'] = new_category.strip()

        return cleaned_data

    def save(self, commit=True):
        product = super().save(commit=False)

        new_category_name = self.cleaned_data.get('new_category')
        if new_category_name:
            category, _ = Category.objects.get_or_create(name=new_category_name)
            product.category = category

        if commit:
            product.save()
            self.save_m2m()

        return product


class StockSupplyForm(forms.ModelForm):
    class Meta:
        model = StockSupply
        fields = [
            'supplier', 'quantity', 'supply_mode',
            'units_per_package', 'packages_per_carton',
            'unit_cost_price', 'unit_sale_price',
            'date', 'notes',
        ]
        help_texts = {
            'supplier': 'Choisis le fournisseur ou laisse vide si inconnu.',
            'quantity': 'Combien de pièces/paquets/cartons reçus ?',
            'supply_mode': 'Es-tu en train de recevoir des pièces, des paquets ou des cartons ?',
            'units_per_package': 'Combien d\'unités dans un paquet ? (ex: 12 bouteilles par paquet)',
            'packages_per_carton': 'Combien de paquets dans un carton ?',
            'unit_cost_price': 'Prix d\'achat d\'une unité (pièce) en FCFA.',
            'unit_sale_price': 'Prix de vente d\'une unité en FCFA. Laisse vide pour garder l\'ancien prix.',
            'notes': 'Infos complémentaires (optionnel).',
        }
        widgets = {
            'supplier': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01', 'min': '0.01'}),
            'supply_mode': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'units_per_package': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01', 'min': '1'}),
            'packages_per_carton': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01', 'min': '1'}),
            'unit_cost_price': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01', 'min': '0'}),
            'unit_sale_price': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01', 'min': '0'}),
            'date': forms.DateInput(attrs={'class': 'form-control form-control-sm', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control form-control-sm', 'rows': 3}),
        }

    def __init__(self, *args, product=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.product = product
        if product and not self.is_bound:
            self.initial.update({
                'units_per_package': product.pack_size or 1,
                'packages_per_carton': product.carton_size or 1,
                'unit_cost_price': product.cost_price or 0,
                'unit_sale_price': self.suggested_sale_price(product),
            })

    def suggested_sale_price(self, product):
        if product.target_margin_percent and product.cost_price:
            return product.cost_price * (1 + product.target_margin_percent / 100)
        return product.price or 0

    def clean(self):
        cleaned_data = super().clean()
        quantity = cleaned_data.get('quantity')
        units_per_package = cleaned_data.get('units_per_package') or 1
        packages_per_carton = cleaned_data.get('packages_per_carton') or 1
        unit_cost_price = cleaned_data.get('unit_cost_price') or 0
        unit_sale_price = cleaned_data.get('unit_sale_price') or 0

        if quantity is not None and quantity <= 0:
            self.add_error('quantity', 'La quantité doit être supérieure à 0.')
        if units_per_package < 1:
            self.add_error('units_per_package', 'Minimum 1 unité par paquet.')
        if packages_per_carton < 1:
            self.add_error('packages_per_carton', 'Minimum 1 paquet par carton.')
        if unit_sale_price and unit_cost_price and unit_sale_price < unit_cost_price:
            self.add_error('unit_sale_price', "Le prix de vente doit être supérieur ou égal au prix d'achat.")

        return cleaned_data

    def calculated_total_units(self):
        quantity = self.cleaned_data['quantity']
        mode = self.cleaned_data['supply_mode']
        units_per_package = self.cleaned_data['units_per_package']
        packages_per_carton = self.cleaned_data['packages_per_carton']
        if mode == 'carton':
            return quantity * units_per_package * packages_per_carton
        if mode == 'paquet':
            return quantity * units_per_package
        return quantity


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'phone', 'address', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'phone': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'address': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'notes': forms.Textarea(attrs={'class': 'form-control form-control-sm', 'rows': 3}),
        }


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'phone', 'address', 'credit_limit', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'phone': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'address': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'credit_limit': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01', 'min': '0'}),
            'notes': forms.Textarea(attrs={'class': 'form-control form-control-sm', 'rows': 3}),
        }


class CashSessionOpenForm(forms.ModelForm):
    class Meta:
        model = CashSession
        fields = ['opening_balance', 'notes']
        widgets = {
            'opening_balance': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01', 'min': '0'}),
            'notes': forms.Textarea(attrs={'class': 'form-control form-control-sm', 'rows': 3}),
        }


class CashSessionCloseForm(forms.ModelForm):
    class Meta:
        model = CashSession
        fields = ['closing_balance', 'notes']
        widgets = {
            'closing_balance': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01', 'min': '0'}),
            'notes': forms.Textarea(attrs={'class': 'form-control form-control-sm', 'rows': 3}),
        }


class CashMovementForm(forms.ModelForm):
    class Meta:
        model = CashMovement
        fields = ['movement_type', 'label', 'amount']
        widgets = {
            'movement_type': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'label': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01', 'min': '0'}),
        }


class InventoryAdjustmentForm(forms.ModelForm):
    class Meta:
        model = InventoryAdjustment
        fields = ['product', 'counted_stock', 'date', 'notes']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'counted_stock': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01', 'min': '0'}),
            'date': forms.DateInput(attrs={'class': 'form-control form-control-sm', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control form-control-sm', 'rows': 3}),
        }


class UserRoleForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['role']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-select form-select-sm'}),
        }


# ======================
# DÉPENSES
# ======================
class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['description', 'amount', 'category', 'date', 'notes']
        widgets = {
            'description': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'category': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'date': forms.DateInput(attrs={'class': 'form-control form-control-sm', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control form-control-sm', 'rows': 3}),
        }


# ======================
# DETTES
# ======================
class DebtForm(forms.ModelForm):
    class Meta:
        model = Debt
        fields = ['debt_type', 'person', 'amount', 'due_date', 'paid', 'notes']
        widgets = {
            'debt_type': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'person': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control form-control-sm', 'type': 'date'}),
            'paid': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control form-control-sm', 'rows': 3}),
        }


# ======================
# CRÉDIT TÉLÉPHONIQUE
# ======================
class PhoneCreditForm(forms.ModelForm):
    class Meta:
        model = PhoneCredit
        fields = ['phone_number', 'operator', 'amount', 'date']
        widgets = {
            'phone_number': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'operator': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'date': forms.DateInput(attrs={'class': 'form-control form-control-sm', 'type': 'date'}),
        }

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')

        if amount is None:
            return amount

        if amount < 10500:
            raise forms.ValidationError("Minimum 10 500 FCFA (10 000 achat + 500 bénéfice).")

        available_stock = PhoneCreditPurchase.get_available_stock()

        if available_stock is None or available_stock < 10000:
            raise forms.ValidationError(
                f"Stock insuffisant. Disponible : {available_stock} FCFA"
            )

        return amount


# ======================
# ACHAT CRÉDIT
# ======================
class PhoneCreditPurchaseForm(forms.ModelForm):
    class Meta:
        model = PhoneCreditPurchase
        fields = ['amount', 'date']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'date': forms.DateInput(attrs={'class': 'form-control form-control-sm', 'type': 'date'}),
        }


class StoreSettingsForm(forms.ModelForm):
    class Meta:
        model = StoreSettings
        fields = [
            'store_name', 'welcome_message', 'scripture_mode', 'language',
            'logo', 'background_image', 'invoice_watermark', 'theme', 'invoice_layout',
            'address', 'phone_number', 'signature', 'voice_alerts', 'currency',
            'eur_rate', 'usd_rate', 'monthly_expense_limit', 'sms_api_url', 'sms_api_key',
            'sms_from', 'whatsapp_api_key', 'whatsapp_phone_number_id',
            'default_bank_account', 'label_layout', 'label_font_size',
            'label_border_style', 'label_columns_screen', 'label_columns_print',
            'label_logo', 'label_show_store_name', 'label_show_barcode',
            'label_show_code',
        ]
        widgets = {
            'store_name': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'data-voice': 'true'}),
            'welcome_message': forms.Textarea(attrs={'class': 'form-control form-control-sm', 'rows': 3, 'placeholder': 'Ex: Bienvenue chez nous !'}),
            'scripture_mode': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'language': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'logo': forms.ClearableFileInput(attrs={'class': 'form-control form-control-sm', 'accept': 'image/*'}),
            'background_image': forms.ClearableFileInput(attrs={'class': 'form-control form-control-sm', 'accept': 'image/*'}),
            'invoice_watermark': forms.ClearableFileInput(attrs={'class': 'form-control form-control-sm', 'accept': 'image/*'}),
            'address': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Ex: 123 Rue du Marché, Bamako'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Ex: +223 00 00 00 00'}),
            'signature': forms.ClearableFileInput(attrs={'class': 'form-control form-control-sm', 'accept': 'image/*'}),
            'voice_alerts': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'theme': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'invoice_layout': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'currency': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'eur_rate': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01', 'min': '0'}),
            'usd_rate': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01', 'min': '0'}),
            'monthly_expense_limit': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'min': '0', 'step': '0.01'}),
            'sms_api_key': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'sms_from': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'whatsapp_api_key': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'whatsapp_phone_number_id': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'default_bank_account': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'label_layout': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'label_font_size': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'label_border_style': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'label_columns_screen': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'min': '1', 'max': '6'}),
            'label_columns_print': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'min': '2', 'max': '8'}),
            'label_logo': forms.ClearableFileInput(attrs={'class': 'form-control form-control-sm', 'accept': 'image/*'}),
            'label_show_store_name': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'label_show_barcode': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'label_show_code': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class AppFeatureForm(forms.ModelForm):
    class Meta:
        model = AppFeature
        fields = ['title', 'description', 'code_notes', 'status']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Ex: ajouter une remise, gérer les fournisseurs...'
            }),
            'description': forms.Textarea(attrs={'class': 'form-control form-control-sm', 'rows': 4}),
            'code_notes': forms.Textarea(attrs={
                'class': 'form-control font-monospace',
                'rows': 6,
                'placeholder': 'Écris ici les fichiers, règles ou morceaux de code à prévoir.'
            }),
            'status': forms.Select(attrs={'class': 'form-select form-select-sm'}),
        }


from django.contrib.auth.forms import AuthenticationForm


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control form-control-sm', 'placeholder': 'Nom d\'utilisateur'
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control form-control-sm', 'placeholder': 'Mot de passe'
        })


class DataImportForm(forms.Form):
    file = forms.FileField(
        label='Fichier JSON',
        widget=forms.FileInput(attrs={'class': 'form-control form-control-sm', 'accept': '.json'})
    )


class AccountCreationForm(UserCreationForm):
    role = forms.ChoiceField(
        choices=UserProfile.ROLE_CHOICES,
        initial='caissier',
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'role', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'data-voice': 'true'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'data-voice': 'true'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'data-voice': 'true'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control form-control-sm'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control form-control-sm'})

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            UserProfile.objects.update_or_create(
                user=user,
                defaults={'role': self.cleaned_data['role']}
            )
        return user


# ======================
# BONS DE COMMANDE
# ======================
class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = ['supplier', 'status', 'date', 'expected_date', 'notes']
        widgets = {
            'supplier': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'status': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'date': forms.DateInput(attrs={'class': 'form-control form-control-sm', 'type': 'date'}),
            'expected_date': forms.DateInput(attrs={'class': 'form-control form-control-sm', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control form-control-sm', 'rows': 3}),
        }


class PurchaseOrderItemForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrderItem
        fields = ['product', 'quantity_ordered', 'unit_price']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'quantity_ordered': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01', 'min': '0.01'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01', 'min': '0'}),
        }


# ======================
# PROMOTIONS / REMISES
# ======================
class PromotionForm(forms.ModelForm):
    class Meta:
        model = Promotion
        fields = ['name', 'discount_type', 'discount_value', 'start_date', 'end_date', 'active', 'products', 'min_purchase', 'applies_to_all']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'data-voice': 'true'}),
            'discount_type': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'discount_value': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01', 'min': '0'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control form-control-sm', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control form-control-sm', 'type': 'date'}),
            'active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'products': forms.SelectMultiple(attrs={'class': 'form-select form-select-sm', 'size': '8'}),
            'min_purchase': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01', 'min': '0'}),
            'applies_to_all': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


# ======================
# RETOURS / ÉCHANGES
# ======================
class ProductReturnForm(forms.ModelForm):
    class Meta:
        model = ProductReturn
        fields = ['sale', 'date', 'reason', 'status', 'refund_amount', 'notes']
        widgets = {
            'sale': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'date': forms.DateInput(attrs={'class': 'form-control form-control-sm', 'type': 'date'}),
            'reason': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'status': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'refund_amount': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01', 'min': '0'}),
            'notes': forms.Textarea(attrs={'class': 'form-control form-control-sm', 'rows': 3}),
        }


# ======================
# COMMANDES CLIENTS
# ======================
class CustomerOrderForm(forms.ModelForm):
    class Meta:
        model = CustomerOrder
        fields = ['customer_name', 'customer_phone', 'customer', 'date', 'pickup_date', 'status', 'deposit', 'notes']
        widgets = {
            'customer_name': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'data-voice': 'true'}),
            'customer_phone': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'customer': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'date': forms.DateInput(attrs={'class': 'form-control form-control-sm', 'type': 'date'}),
            'pickup_date': forms.DateInput(attrs={'class': 'form-control form-control-sm', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'deposit': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01', 'min': '0'}),
            'notes': forms.Textarea(attrs={'class': 'form-control form-control-sm', 'rows': 3}),
        }


class StockLossForm(forms.ModelForm):
    class Meta:
        model = StockLoss
        fields = ['product', 'quantity', 'loss_amount', 'date', 'reason', 'notes']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'loss_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'readonly': 'readonly'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'reason': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


# ======================
# RETOURS FOURNISSEURS
# ======================
class SupplierReturnForm(forms.ModelForm):
    class Meta:
        model = SupplierReturn
        fields = ['supplier', 'date', 'reason', 'status', 'notes']
        widgets = {
            'supplier': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'date': forms.DateInput(attrs={'class': 'form-control form-control-sm', 'type': 'date'}),
            'reason': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'status': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'notes': forms.Textarea(attrs={'class': 'form-control form-control-sm', 'rows': 3}),
        }


class SupplierReturnItemForm(forms.ModelForm):
    class Meta:
        model = SupplierReturnItem
        fields = ['product', 'quantity', 'unit_cost', 'reason']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01', 'min': '0.01'}),
            'unit_cost': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01', 'min': '0'}),
            'reason': forms.Select(attrs={'class': 'form-select form-select-sm'}),
        }


# ======================
# BANQUES
# ======================
class BankAccountForm(forms.ModelForm):
    class Meta:
        model = BankAccount
        fields = ['name', 'account_number', 'bank_name', 'balance', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'data-voice': 'true'}),
            'account_number': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'bank_name': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'balance': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01', 'min': '0'}),
            'notes': forms.Textarea(attrs={'class': 'form-control form-control-sm', 'rows': 3}),
        }


class BankTransactionForm(forms.ModelForm):
    class Meta:
        model = BankTransaction
        fields = ['account', 'transaction_type', 'amount', 'date', 'description', 'reference', 'notes']
        widgets = {
            'account': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'transaction_type': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01', 'min': '0.01'}),
            'date': forms.DateInput(attrs={'class': 'form-control form-control-sm', 'type': 'date'}),
            'description': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'reference': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'notes': forms.Textarea(attrs={'class': 'form-control form-control-sm', 'rows': 3}),
        }


# ======================
# FIDÉLITÉ
# ======================
class SolarComponentForm(forms.ModelForm):
    class Meta:
        model = SolarComponent
        fields = ['name', 'category', 'unit_price', 'cost_price', 'stock', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'data-voice': 'true'}),
            'category': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01', 'min': '0'}),
            'cost_price': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01', 'min': '0'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01', 'min': '0'}),
            'notes': forms.Textarea(attrs={'class': 'form-control form-control-sm', 'rows': 3}),
        }


class SolarProjectItemForm(forms.ModelForm):
    class Meta:
        model = SolarProjectItem
        fields = ['component', 'designation', 'quantity', 'unit_price', 'cost_price']
        widgets = {
            'component': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'designation': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'data-voice': 'true', 'placeholder': 'Ex: Panneau 300Wc monocristallin'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01', 'min': '0.01'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01', 'min': '0'}),
            'cost_price': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01', 'min': '0'}),
        }


class SolarProjectForm(forms.ModelForm):
    class Meta:
        model = SolarProject
        fields = ['client_name', 'client_phone', 'client_address', 'date', 'status',
                   'system_type', 'capacity_kw', 'total_cost', 'total_price', 'deposit',
                   'actual_profit', 'won_date', 'notes']
        widgets = {
            'client_name': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'data-voice': 'true'}),
            'client_phone': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'client_address': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'date': forms.DateInput(attrs={'class': 'form-control form-control-sm', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'system_type': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'capacity_kw': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01', 'min': '0'}),
            'total_cost': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01', 'min': '0'}),
            'total_price': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01', 'min': '0'}),
            'deposit': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01', 'min': '0'}),
            'actual_profit': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01'}),
            'won_date': forms.DateInput(attrs={'class': 'form-control form-control-sm', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control form-control-sm', 'rows': 3}),
        }


class LoyaltyProgramForm(forms.ModelForm):
    class Meta:
        model = LoyaltyProgram
        fields = ['name', 'points_per_purchase', 'points_value', 'min_points_to_redeem', 'active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'points_per_purchase': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01', 'min': '0'}),
            'points_value': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01', 'min': '0'}),
            'min_points_to_redeem': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01', 'min': '0'}),
            'active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class EmployeeCreateForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['first_name', 'last_name', 'phone', 'email', 'role', 'salary', 'hire_date', 'is_active', 'notes']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'phone': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'email': forms.EmailInput(attrs={'class': 'form-control form-control-sm'}),
            'role': forms.Select(attrs={'class': 'form-control form-control-sm'}),
            'salary': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '1', 'min': '0'}),
            'hire_date': forms.DateInput(attrs={'class': 'form-control form-control-sm', 'type': 'date'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control form-control-sm', 'rows': 3}),
        }
