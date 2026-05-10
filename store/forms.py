from datetime import date

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import (
    Category, Debt, Expense,
    PhoneCredit, PhoneCreditPurchase,
    Product, StoreSettings, AppFeature
)

# ======================
# VENTE SIMPLE
# ======================
class SaleForm(forms.Form):
    product = forms.ModelChoiceField(
        queryset=Product.objects.filter(stock__gt=0),
        label='Produit',
        empty_label='Choisir un produit',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    quantity = forms.DecimalField(
        min_value=0.01,
        max_digits=10,
        decimal_places=2,
        label='Quantité',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )


class AIFeatureInstructionForm(forms.Form):
    instruction = forms.CharField(
        label='Instruction pour l’IA',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Ex: ajoute une remise automatique pour les ventes de pain et de glaces...'
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
        label='Nouvelle catégorie',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: Alimentation, Boisson...'
        })
    )

    image_url = forms.URLField(
        required=False,
        label='URL de l\'image (Google)',
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'Colle l\'URL d\'une image trouvée sur Google...'
        })
    )

    class Meta:
        model = Product
        fields = [
            'code', 'name', 'image',
            'category',
            'unit', 'price', 'cost_price',
            'stock', 'min_stock', 'expiry_date',
            'pack_size', 'pack_price',
        ]

        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Automatique si vide'
            }),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'unit': forms.Select(attrs={'class': 'form-select'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'cost_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'min_stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'pack_size': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 12 pour une boîte de 12'}),
            'pack_price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Laissez vide = prix unitaire × taille'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ('unit', 'cost_price', 'stock', 'min_stock', 'pack_size'):
            self.fields[field].required = False

    def clean(self):
        cleaned_data = super().clean()

        price = cleaned_data.get('price')
        cost_price = cleaned_data.get('cost_price')
        expiry_date = cleaned_data.get('expiry_date')
        new_category = cleaned_data.get('new_category')

        if price and cost_price and price < cost_price:
            self.add_error('price', "Le prix de vente doit être supérieur ou égal au prix d'achat.")

        if expiry_date and expiry_date < date.today():
            self.add_error('expiry_date', "Date invalide (déjà passée).")

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


# ======================
# DÉPENSES
# ======================
class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['description', 'amount', 'category', 'date', 'notes']
        widgets = {
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


# ======================
# DETTES
# ======================
class DebtForm(forms.ModelForm):
    class Meta:
        model = Debt
        fields = ['debt_type', 'person', 'amount', 'due_date', 'paid', 'notes']
        widgets = {
            'debt_type': forms.Select(attrs={'class': 'form-select'}),
            'person': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'paid': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


# ======================
# CRÉDIT TÉLÉPHONIQUE
# ======================
class PhoneCreditForm(forms.ModelForm):
    class Meta:
        model = PhoneCredit
        fields = ['phone_number', 'operator', 'amount', 'date']
        widgets = {
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'operator': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
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
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class StoreSettingsForm(forms.ModelForm):
    class Meta:
        model = StoreSettings
        fields = ['store_name', 'welcome_message', 'language', 'logo', 'background_image', 'invoice_watermark', 'theme', 'invoice_layout', 'address', 'phone_number', 'signature', 'voice_alerts', 'monthly_expense_limit']
        widgets = {
            'store_name': forms.TextInput(attrs={'class': 'form-control'}),
            'welcome_message': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Ex: Bienvenue chez nous !'}),
            'language': forms.Select(attrs={'class': 'form-select'}),
            'logo': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'background_image': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'invoice_watermark': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 123 Rue du Marché, Bamako'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: +223 00 00 00 00'}),
            'signature': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'voice_alerts': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'theme': forms.Select(attrs={'class': 'form-select'}),
            'invoice_layout': forms.Select(attrs={'class': 'form-select'}),
            'monthly_expense_limit': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
        }


class AppFeatureForm(forms.ModelForm):
    class Meta:
        model = AppFeature
        fields = ['title', 'description', 'code_notes', 'status']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: ajouter une remise, gérer les fournisseurs...'
            }),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'code_notes': forms.Textarea(attrs={
                'class': 'form-control font-monospace',
                'rows': 6,
                'placeholder': 'Écris ici les fichiers, règles ou morceaux de code à prévoir.'
            }),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


from django.contrib.auth.forms import AuthenticationForm


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control', 'placeholder': 'Nom d\'utilisateur'
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control', 'placeholder': 'Mot de passe'
        })


class DataImportForm(forms.Form):
    file = forms.FileField(
        label='Fichier JSON',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.json'})
    )


class AccountCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
