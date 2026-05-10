from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum

class Category(models.Model):
    name = models.CharField(max_length=150, unique=True)

    class Meta:
        verbose_name = 'Catégorie'
        verbose_name_plural = 'Catégories'
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    code = models.CharField('Code article', max_length=50, unique=True, blank=True)
    name = models.CharField(max_length=200)
    image = models.FileField('Image article', upload_to='products/', blank=True)
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL, related_name='products')
    unit = models.CharField('Unité', max_length=20, choices=[
        ('kg', 'Kilogramme'),
        ('l', 'Litre'),
        ('pièce', 'Pièce'),
        ('sachet', 'Sachet'),
        ('boîte', 'Boîte'),
    ], default='pièce')
    price = models.DecimalField('Prix de vente (FCFA)', max_digits=10, decimal_places=2)
    cost_price = models.DecimalField('Prix d\'achat (FCFA)', max_digits=10, decimal_places=2, default=0)
    stock = models.DecimalField('Stock', max_digits=10, decimal_places=2, default=0)
    min_stock = models.DecimalField('Stock minimum', max_digits=10, decimal_places=2, default=0)
    expiry_date = models.DateField('Date de péremption', null=True, blank=True)
    pack_size = models.DecimalField('Taille paquet', max_digits=10, decimal_places=2, default=1)
    pack_price = models.DecimalField('Prix du paquet (FCFA)', max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f'{self.code} - {self.name} ({self.stock} {self.unit})'

    def save(self, *args, **kwargs):
        if not self.code:
            last_product = Product.objects.exclude(code='').order_by('-id').first()
            next_number = (last_product.id + 1) if last_product else 1
            code = f'ART-{next_number:05d}'
            while Product.objects.filter(code=code).exists():
                next_number += 1
                code = f'ART-{next_number:05d}'
            self.code = code
        super().save(*args, **kwargs)

    def clean(self):
        if self.price is not None and self.cost_price is not None and self.price < self.cost_price:
            raise ValidationError({'price': "Le prix de vente doit être supérieur ou égal au prix d'achat."})
        if self.expiry_date and self.expiry_date < date.today():
            raise ValidationError({'expiry_date': "La date de péremption doit être aujourd'hui ou ultérieure."})

    @property
    def is_available(self):
        return self.stock > 0

    @property
    def needs_restock(self):
        return self.stock <= self.min_stock

class Sale(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sale_date = models.DateField('Date de vente', default=date.today)
    notes = models.TextField('Notes', blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Vente #{self.id or "?"} - {self.sale_date:%Y-%m-%d %H:%M}'

    def calculate_total(self):
        return sum(item.subtotal for item in self.items.all())

    def update_total(self):
        self.total = self.calculate_total()
        self.save(update_fields=['total'])

class SaleItem(models.Model):
    SALE_MODE_CHOICES = [
        ('detail', 'Détail'),
        ('paquet', 'Paquet'),
    ]

    sale = models.ForeignKey(Sale, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    sale_mode = models.CharField('Mode de vente', max_length=10, choices=SALE_MODE_CHOICES, default='detail')

    class Meta:
        verbose_name = 'Ligne de vente'
        verbose_name_plural = 'Lignes de vente'

    def __str__(self):
        return f'{self.quantity} x {self.product.name}'

    @property
    def subtotal(self):
        return self.quantity * self.price


class Expense(models.Model):
    CATEGORY_CHOICES = [
        ('carburant', 'Carburant'),
        ('credit_telephonique', 'Crédit téléphonique'),
        ('nourriture', 'Nourriture'),
        ('loyer', 'Loyer'),
        ('wifi', 'Abonnement wifi'),
        ('salaire_proprietaire', 'Mon salaire'),
        ('salaire_employe', 'Salaire employé'),
        ('autre', 'Autre'),
    ]

    description = models.CharField(max_length=200)
    amount = models.DecimalField('Montant (FCFA)', max_digits=10, decimal_places=2)
    category = models.CharField('Catégorie', max_length=120, choices=CATEGORY_CHOICES, default='autre')
    date = models.DateField(default=date.today)
    notes = models.TextField('Notes', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = 'Dépense'
        verbose_name_plural = 'Dépenses'

    def __str__(self):
        return f'{self.description} - {self.amount} FCFA'


class Debt(models.Model):
    DEBT_TYPE_CHOICES = [
        ('payable', 'À payer'),
        ('receivable', 'À recevoir'),
    ]

    debt_type = models.CharField('Type', max_length=10, choices=DEBT_TYPE_CHOICES, default='payable')
    person = models.CharField('Contact', max_length=150)
    amount = models.DecimalField('Montant (FCFA)', max_digits=10, decimal_places=2)
    due_date = models.DateField('Date d’échéance')
    paid = models.BooleanField('Réglée', default=False)
    paid_at = models.DateTimeField('Date de paiement', null=True, blank=True)
    notes = models.TextField('Notes', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['paid', 'due_date']
        verbose_name = 'Dette'
        verbose_name_plural = 'Dettes'

    def __str__(self):
        return f'{self.person} - {self.amount} FCFA ({self.get_debt_type_display()})'

    @property
    def status(self):
        if self.paid:
            return 'Réglée'
        if self.due_date < date.today():
            return 'En retard'
        return 'En attente'


class PhoneCredit(models.Model):
    OPERATOR_CHOICES = [
        ('orange_ml', 'Orange Mali'),
        ('malitel', 'Malitel'),
    ]

    phone_number = models.CharField('Numéro de téléphone', max_length=20)
    operator = models.CharField('Opérateur', max_length=10, choices=OPERATOR_CHOICES)
    amount = models.DecimalField('Montant payé (FCFA)', max_digits=10, decimal_places=2)
    date = models.DateField('Date', default=date.today)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = 'Crédit téléphonique'
        verbose_name_plural = 'Crédits téléphoniques'

    def __str__(self):
        return f'{self.phone_number} - {self.amount} FCFA ({self.get_operator_display()})'

    @property
    def cost_price(self):
        return Decimal('10000.00')  # Prix d'achat fixe

    @property
    def profit(self):
        return Decimal('500.00')  # Bénéfice fixe

    @property
    def credit_amount(self):
        return self.amount - self.profit  # Montant du crédit transféré


class PhoneCreditPurchase(models.Model):
    amount = models.DecimalField('Montant acheté (FCFA)', max_digits=10, decimal_places=2, default=10000.00)
    date = models.DateField('Date', default=date.today)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = 'Achat de crédits téléphoniques'
        verbose_name_plural = 'Achats de crédits téléphoniques'

    def __str__(self):
        return f'Achat de {self.amount} FCFA - {self.date}'

    @staticmethod
    def get_available_stock():
        total_purchased = PhoneCreditPurchase.objects.aggregate(total=Sum('amount'))['total'] or 0
        total_used = PhoneCredit.objects.count() * Decimal('10000.00')
        return total_purchased - total_used


class StoreSettings(models.Model):
    THEME_CHOICES = [
        ('burgundy', 'Rouge bordeaux'),
        ('blue', 'Bleu moderne'),
        ('green', 'Vert commerce'),
        ('dark', 'Sombre'),
        ('light', 'Clair'),
    ]

    INVOICE_LAYOUT_CHOICES = [
        ('classic', 'Classique'),
        ('compact', 'Compacte'),
        ('modern', 'Moderne'),
    ]

    LANGUAGE_CHOICES = [
        ('fr', 'Français'),
        ('en', 'English'),
    ]

    store_name = models.CharField('Nom du magasin', max_length=150, default='Supermarché')
    welcome_message = models.TextField('Message de bienvenue', blank=True, default='')
    language = models.CharField('Langue', max_length=5, choices=LANGUAGE_CHOICES, default='fr')
    logo = models.FileField('Logo', upload_to='logos/', blank=True)
    background_image = models.FileField('Image de fond', upload_to='backgrounds/', blank=True)
    invoice_watermark = models.FileField('Filigrane facture', upload_to='watermarks/', blank=True)
    theme = models.CharField('Thème', max_length=20, choices=THEME_CHOICES, default='blue')
    invoice_layout = models.CharField(
        'Disposition de facture',
        max_length=20,
        choices=INVOICE_LAYOUT_CHOICES,
        default='classic',
    )
    address = models.CharField('Adresse du magasin', max_length=300, blank=True, default='')
    phone_number = models.CharField('Numéro de téléphone', max_length=30, blank=True, default='')
    signature = models.FileField('Signature fournisseur', upload_to='signatures/', blank=True)
    voice_alerts = models.BooleanField('Alertes vocales stock faible', default=False)
    monthly_expense_limit = models.DecimalField(
        'Limite mensuelle de dépenses (FCFA)',
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    class Meta:
        verbose_name = 'Paramètres du magasin'
        verbose_name_plural = 'Paramètres du magasin'

    def __str__(self):
        return self.store_name

    @classmethod
    def load(cls):
        settings, _ = cls.objects.get_or_create(pk=1)
        return settings


class AppFeature(models.Model):
    STATUS_CHOICES = [
        ('idea', 'Idée'),
        ('planned', 'À faire'),
        ('coding', 'En cours'),
        ('done', 'Terminé'),
    ]

    title = models.CharField('Fonctionnalité', max_length=180)
    description = models.TextField('Description')
    code_notes = models.TextField('Notes de code', blank=True)
    status = models.CharField('Statut', max_length=20, choices=STATUS_CHOICES, default='idea')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['status', '-updated_at']
        verbose_name = 'Fonctionnalité'
        verbose_name_plural = 'Fonctionnalités'

    def __str__(self):
        return self.title

