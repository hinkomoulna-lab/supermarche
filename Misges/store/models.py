from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
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


class Supplier(models.Model):
    name = models.CharField('Fournisseur', max_length=180, unique=True)
    phone = models.CharField('Téléphone', max_length=30, blank=True)
    address = models.CharField('Adresse', max_length=250, blank=True)
    notes = models.TextField('Notes', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Fournisseur'
        verbose_name_plural = 'Fournisseurs'

    def __str__(self):
        return self.name


class Customer(models.Model):
    name = models.CharField('Client', max_length=180)
    phone = models.CharField('Téléphone', max_length=30, blank=True)
    address = models.CharField('Adresse', max_length=250, blank=True)
    notes = models.TextField('Notes', blank=True)
    credit_limit = models.DecimalField('Plafond de crédit (FCFA)', max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def outstanding_balance(self):
        total = self.sales.filter(payment_status__in=['partial', 'credit']).aggregate(
            total=models.Sum(models.F('total') - models.F('amount_paid'))
        )['total'] or 0
        return total

    @property
    def credit_available(self):
        if self.credit_limit == 0:
            return Decimal('Inf')
        return max(self.credit_limit - self.outstanding_balance, 0)

    class Meta:
        ordering = ['name']
        verbose_name = 'Client'
        verbose_name_plural = 'Clients'

    def __str__(self):
        return self.name


class Product(models.Model):
    code = models.CharField('Code article', max_length=50, unique=True, blank=True)
    barcode = models.CharField('Code-barres', max_length=80, unique=True, blank=True, null=True)
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
    carton_size = models.DecimalField('Paquets par carton', max_digits=10, decimal_places=2, default=1)
    target_margin_percent = models.DecimalField('Marge cible (%)', max_digits=5, decimal_places=2, default=0)
    tax_rate = models.DecimalField('TVA (%)', max_digits=5, decimal_places=2, default=0)
    price_eur = models.DecimalField('Prix de vente (EUR)', max_digits=10, decimal_places=2, null=True, blank=True)
    price_usd = models.DecimalField('Prix de vente (USD)', max_digits=10, decimal_places=2, null=True, blank=True)
    is_composite = models.BooleanField('Produit composite (recette)', default=False)
    min_stock = models.DecimalField('Stock minimum (alerte)', max_digits=10, decimal_places=2, default=0)

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

    @property
    def is_available(self):
        return self.stock > 0

    @property
    def needs_restock(self):
        return self.stock <= self.min_stock

    @property
    def almost_expired(self):
        if not self.expiry_date:
            return False
        from datetime import timedelta
        return date.today() + timedelta(days=30) >= self.expiry_date >= date.today()

    @property
    def is_expired(self):
        if not self.expiry_date:
            return False
        return self.expiry_date < date.today()

    @property
    def days_until_expiry(self):
        if not self.expiry_date:
            return None
        delta = (self.expiry_date - date.today()).days
        return delta if delta >= 0 else None

    def units_for_mode(self, quantity, mode):
        quantity = Decimal(quantity)
        if mode in ('paquet', 'cartouche') and self.pack_size > 1:
            return quantity * self.pack_size
        if mode == 'carton' and self.pack_size > 1 and self.carton_size > 1:
            return quantity * self.pack_size * self.carton_size
        return quantity

    def sale_price_for_mode(self, mode):
        if mode in ('paquet', 'cartouche') and self.pack_size > 1:
            return self.pack_price or (self.price * self.pack_size)
        if mode == 'carton' and self.pack_size > 1 and self.carton_size > 1:
            pack_price = self.pack_price or (self.price * self.pack_size)
            return pack_price * self.carton_size
        return self.price


class PurchasePriceHistory(models.Model):
    product = models.ForeignKey(Product, related_name='price_history', on_delete=models.CASCADE, verbose_name='Produit')
    old_price = models.DecimalField('Ancien prix d\'achat', max_digits=10, decimal_places=2)
    new_price = models.DecimalField('Nouveau prix d\'achat', max_digits=10, decimal_places=2)
    source = models.CharField('Source', max_length=20, choices=[
        ('manual', 'Modification manuelle'),
        ('supply', 'Approvisionnement'),
    ], default='manual')
    changed_at = models.DateTimeField('Date de modification', auto_now_add=True)

    class Meta:
        ordering = ['-changed_at']
        verbose_name = 'Historique prix d\'achat'
        verbose_name_plural = 'Historique des prix d\'achat'

    def __str__(self):
        return f'{self.product.name}: {self.old_price} → {self.new_price} ({self.changed_at:%d/%m/%Y})'


class StockSupply(models.Model):
    SUPPLY_MODE_CHOICES = [
        ('piece', 'Pièce'),
        ('paquet', 'Paquet'),
        ('carton', 'Carton'),
    ]

    product = models.ForeignKey(Product, related_name='supplies', on_delete=models.CASCADE)
    supplier = models.ForeignKey(Supplier, related_name='supplies', null=True, blank=True, on_delete=models.SET_NULL)
    quantity = models.DecimalField('Quantité reçue', max_digits=10, decimal_places=2)
    supply_mode = models.CharField('Conditionnement', max_length=10, choices=SUPPLY_MODE_CHOICES, default='piece')
    units_per_package = models.DecimalField('Unités par paquet', max_digits=10, decimal_places=2, default=1)
    packages_per_carton = models.DecimalField('Paquets par carton', max_digits=10, decimal_places=2, default=1)
    total_units = models.DecimalField('Unités ajoutées au stock', max_digits=10, decimal_places=2, default=0)
    unit_cost_price = models.DecimalField('Prix d\'achat unitaire (FCFA)', max_digits=10, decimal_places=2, default=0)
    unit_sale_price = models.DecimalField('Prix de vente unitaire (FCFA)', max_digits=10, decimal_places=2, default=0)
    total_cost = models.DecimalField('Coût total approvisionnement (FCFA)', max_digits=12, decimal_places=2, default=0)
    date = models.DateField('Date d\'approvisionnement', default=date.today)
    notes = models.TextField('Notes', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = 'Approvisionnement'
        verbose_name_plural = 'Approvisionnements'

    def __str__(self):
        return f'{self.product.name} +{self.total_units} unités'

class Sale(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('paid', 'Payée'),
        ('partial', 'Paiement partiel'),
        ('credit', 'Crédit client'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Espèces'),
        ('orange_money', 'Orange Money'),
        ('malitel_momo', 'Malitel MoMo'),
        ('mixte', 'Mixte'),
    ]

    customer = models.ForeignKey(Customer, related_name='sales', null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amount_paid = models.DecimalField('Montant payé (FCFA)', max_digits=10, decimal_places=2, default=0)
    payment_status = models.CharField('Statut paiement', max_length=10, choices=PAYMENT_STATUS_CHOICES, default='paid')
    payment_method = models.CharField('Mode de paiement', max_length=15, choices=PAYMENT_METHOD_CHOICES, default='cash')
    payment_phone = models.CharField('Téléphone mobile money', max_length=30, blank=True, default='')
    sale_date = models.DateField('Date de vente', default=date.today)
    sale_time = models.TimeField('Heure de vente', null=True, blank=True)
    customer_name = models.CharField('Nom & prénom du client', max_length=200, blank=True, default='')
    customer_phone = models.CharField('Téléphone client', max_length=30, blank=True, default='')
    notes = models.TextField('Notes', blank=True)
    currency = models.CharField('Devise', max_length=3, default='XOF')
    total_ht = models.DecimalField('Total HT', max_digits=10, decimal_places=2, default=0)
    total_tva = models.DecimalField('Total TVA', max_digits=10, decimal_places=2, default=0)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Vente #{self.id or "?"} - {self.sale_date:%Y-%m-%d %H:%M}'

    def calculate_total(self):
        return sum(item.subtotal for item in self.items.all())

    def update_total(self):
        self.total = self.calculate_total()
        self.save(update_fields=['total'])

    @property
    def balance_due(self):
        balance = self.total - (self.amount_paid or 0)
        return balance if balance > 0 else Decimal('0')

    def sync_payment_status(self):
        if self.amount_paid >= self.total:
            self.payment_status = 'paid'
        elif self.amount_paid > 0:
            self.payment_status = 'partial'
        else:
            self.payment_status = 'credit'

class SaleItem(models.Model):
    SALE_MODE_CHOICES = [
        ('detail', 'Détail'),
        ('piece', 'Pièce'),
        ('paquet', 'Paquet'),
        ('carton', 'Carton'),
        ('cartouche', 'Cartouche'),
        ('kg', 'Kg'),
        ('l', 'L'),
    ]

    sale = models.ForeignKey(Sale, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    sale_mode = models.CharField('Mode de vente', max_length=10, choices=SALE_MODE_CHOICES, default='piece')

    class Meta:
        verbose_name = 'Ligne de vente'
        verbose_name_plural = 'Lignes de vente'

    def __str__(self):
        return f'{self.quantity} x {self.product.name}'

    @property
    def subtotal(self):
        return self.quantity * self.price


class Expense(models.Model):
    INVESTMENT_CATEGORY_KEYS = ('amenagement_boutique', 'achat_materiel')

    CATEGORY_CHOICES = [
        ('amenagement_boutique', 'Aménagement boutique'),
        ('achat_materiel', 'Achat matériel'),
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


class CashSession(models.Model):
    opened_at = models.DateTimeField('Ouverture', auto_now_add=True)
    closed_at = models.DateTimeField('Fermeture', null=True, blank=True)
    opening_balance = models.DecimalField('Fond de caisse (FCFA)', max_digits=12, decimal_places=2, default=0)
    closing_balance = models.DecimalField('Montant réel clôture (FCFA)', max_digits=12, decimal_places=2, null=True, blank=True)
    notes = models.TextField('Notes', blank=True)

    class Meta:
        ordering = ['-opened_at']
        verbose_name = 'Session de caisse'
        verbose_name_plural = 'Sessions de caisse'

    def __str__(self):
        return f'Caisse du {self.opened_at:%d/%m/%Y}'

    @property
    def expected_balance(self):
        sales_total = self.movements.filter(movement_type='sale').aggregate(total=Sum('amount'))['total'] or 0
        out_total = self.movements.filter(movement_type='out').aggregate(total=Sum('amount'))['total'] or 0
        in_total = self.movements.filter(movement_type='in').aggregate(total=Sum('amount'))['total'] or 0
        return self.opening_balance + sales_total + in_total - out_total

    @property
    def cash_gap(self):
        if self.closing_balance is None:
            return Decimal('0')
        return self.closing_balance - self.expected_balance


class CashMovement(models.Model):
    MOVEMENT_CHOICES = [
        ('sale', 'Vente'),
        ('in', 'Entrée caisse'),
        ('out', 'Sortie caisse'),
    ]

    session = models.ForeignKey(CashSession, related_name='movements', on_delete=models.CASCADE)
    movement_type = models.CharField('Type', max_length=10, choices=MOVEMENT_CHOICES, default='in')
    label = models.CharField('Libellé', max_length=180)
    amount = models.DecimalField('Montant (FCFA)', max_digits=12, decimal_places=2)
    sale = models.ForeignKey(Sale, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Mouvement de caisse'
        verbose_name_plural = 'Mouvements de caisse'

    def __str__(self):
        return f'{self.get_movement_type_display()} - {self.amount} FCFA'


class InventoryAdjustment(models.Model):
    product = models.ForeignKey(Product, related_name='inventory_adjustments', on_delete=models.CASCADE)
    system_stock = models.DecimalField('Stock système', max_digits=10, decimal_places=2)
    counted_stock = models.DecimalField('Stock compté', max_digits=10, decimal_places=2)
    difference = models.DecimalField('Écart', max_digits=10, decimal_places=2, default=0)
    date = models.DateField('Date inventaire', default=date.today)
    notes = models.TextField('Notes', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = 'Ajustement inventaire'
        verbose_name_plural = 'Ajustements inventaire'

    def __str__(self):
        return f'{self.product.name}: {self.difference}'


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('gerant', 'Gérant'),
        ('caissier', 'Caissier'),
    ]

    user = models.OneToOneField(User, related_name='store_profile', on_delete=models.CASCADE)
    role = models.CharField('Rôle', max_length=20, choices=ROLE_CHOICES, default='caissier')

    class Meta:
        verbose_name = 'Profil utilisateur'
        verbose_name_plural = 'Profils utilisateur'

    def __str__(self):
        return f'{self.user.username} - {self.get_role_display()}'


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
        ('cyber', 'Cyber futuriste'),
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

    SCRIPTURE_CHOICES = [
        ('bible', 'Bible'),
        ('quran', 'Coran'),
        ('both', 'Bible et Coran'),
        ('none', 'Désactivé'),
    ]
    LABEL_LAYOUT_CHOICES = [
        ('compact', 'Compacte'),
        ('detailed', 'Détaillée'),
        ('minimal', 'Minimale'),
    ]
    LABEL_FONT_SIZE_CHOICES = [
        ('small', 'Petite'),
        ('medium', 'Moyenne'),
        ('large', 'Grande'),
    ]
    LABEL_BORDER_STYLE_CHOICES = [
        ('solid', 'Trait plein'),
        ('dashed', 'Traitillé'),
        ('dotted', 'Pointillé'),
        ('none', 'Aucune'),
    ]

    store_name = models.CharField('Nom du magasin', max_length=150, default='Supermarché')
    welcome_message = models.TextField('Message de bienvenue', blank=True, default='')
    scripture_mode = models.CharField('Textes spirituels', max_length=10, choices=SCRIPTURE_CHOICES, default='bible', blank=True)
    language = models.CharField('Langue', max_length=5, choices=LANGUAGE_CHOICES, default='fr')
    logo = models.FileField('Logo', upload_to='logos/', blank=True)
    background_image = models.FileField('Image de fond', upload_to='backgrounds/', blank=True)
    invoice_watermark = models.FileField('Filigrane facture', upload_to='watermarks/', blank=True)
    theme = models.CharField('Thème', max_length=20, choices=THEME_CHOICES, default='burgundy')
    invoice_layout = models.CharField(
        'Disposition de facture',
        max_length=20,
        choices=INVOICE_LAYOUT_CHOICES,
        default='classic',
    )
    address = models.CharField('Adresse du magasin', max_length=300, blank=True, default='')
    phone_number = models.CharField('Numéro de téléphone', max_length=30, blank=True, default='')
    signature = models.FileField('Signature fournisseur', upload_to='signatures/', blank=True)
    currency = models.CharField('Devise par défaut', max_length=5, choices=[
        ('XOF', 'FCFA (XOF)'),
        ('EUR', 'Euro (EUR)'),
        ('USD', 'Dollar (USD)'),
    ], default='XOF')
    eur_rate = models.DecimalField('Taux 1 EUR = X FCFA', max_digits=10, decimal_places=2, default=655.96)
    usd_rate = models.DecimalField('Taux 1 USD = X FCFA', max_digits=10, decimal_places=2, default=600.00)
    voice_alerts = models.BooleanField('Alertes vocales stock faible', default=False)
    monthly_expense_limit = models.DecimalField(
        'Limite mensuelle de dépenses (FCFA)',
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    # SMS / WhatsApp
    sms_api_url = models.CharField('URL API SMS', max_length=300, blank=True, default='', help_text='URL du gateway SMS (ex: https://api.africastalking.com/version1/messaging)')
    sms_api_key = models.CharField('Clé API SMS', max_length=250, blank=True, default='')
    sms_from = models.CharField('Expéditeur SMS', max_length=20, blank=True, default='')
    whatsapp_api_key = models.CharField('Clé API WhatsApp', max_length=250, blank=True, default='')
    whatsapp_phone_number_id = models.CharField('ID téléphone WhatsApp', max_length=50, blank=True, default='')

    # Bank reconciliation default account
    default_bank_account = models.ForeignKey('BankAccount', null=True, blank=True, on_delete=models.SET_NULL, verbose_name='Compte bancaire par défaut')

    # Price labels
    label_layout = models.CharField('Disposition étiquettes', max_length=20, choices=LABEL_LAYOUT_CHOICES, default='compact')
    label_font_size = models.CharField('Taille de police', max_length=10, choices=LABEL_FONT_SIZE_CHOICES, default='medium')
    label_border_style = models.CharField('Style de bordure', max_length=10, choices=LABEL_BORDER_STYLE_CHOICES, default='dashed')
    label_columns_screen = models.PositiveIntegerField("Colonnes à l'écran", default=2, help_text="Nombre de colonnes sur l'écran (1-6)")
    label_columns_print = models.PositiveIntegerField("Colonnes à l'impression", default=4, help_text="Nombre de colonnes à l'impression (2-8)")
    label_logo = models.FileField('Logo étiquettes', upload_to='label_logos/', blank=True, help_text='Logo spécifique pour les étiquettes')
    label_show_store_name = models.BooleanField('Afficher le nom du magasin', default=True)
    label_show_barcode = models.BooleanField('Afficher le code-barres', default=True)
    label_show_code = models.BooleanField('Afficher le code produit', default=False)

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


class PurchaseOrder(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Brouillon'),
        ('sent', 'Envoyée'),
        ('partial', 'Partiellement reçue'),
        ('received', 'Reçue'),
        ('cancelled', 'Annulée'),
    ]

    supplier = models.ForeignKey(Supplier, related_name='purchase_orders', null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField('Statut', max_length=10, choices=STATUS_CHOICES, default='draft')
    date = models.DateField('Date de commande', default=date.today)
    expected_date = models.DateField('Date de livraison prévue', null=True, blank=True)
    total = models.DecimalField('Total (FCFA)', max_digits=12, decimal_places=2, default=0)
    notes = models.TextField('Notes', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = 'Bon de commande'
        verbose_name_plural = 'Bons de commande'

    def __str__(self):
        return f'Commande #{self.id} - {self.supplier.name if self.supplier else "N/A"} ({self.get_status_display()})'

    def update_total(self):
        self.total = sum(item.subtotal for item in self.items.all())
        self.save(update_fields=['total'])


class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity_ordered = models.DecimalField('Quantité commandée', max_digits=10, decimal_places=2)
    quantity_received = models.DecimalField('Quantité reçue', max_digits=10, decimal_places=2, default=0)
    unit_price = models.DecimalField('Prix unitaire (FCFA)', max_digits=10, decimal_places=2, default=0)

    class Meta:
        verbose_name = 'Ligne de commande'
        verbose_name_plural = 'Lignes de commande'

    def __str__(self):
        return f'{self.product.name} x {self.quantity_ordered}'

    @property
    def subtotal(self):
        return self.quantity_ordered * self.unit_price

    @property
    def remaining(self):
        return self.quantity_ordered - self.quantity_received


class Promotion(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Pourcentage (%)'),
        ('fixed', 'Montant fixe (FCFA)'),
    ]

    name = models.CharField('Nom', max_length=200)
    discount_type = models.CharField('Type de remise', max_length=10, choices=DISCOUNT_TYPE_CHOICES, default='percentage')
    discount_value = models.DecimalField('Valeur de la remise', max_digits=10, decimal_places=2)
    start_date = models.DateField('Date de début')
    end_date = models.DateField('Date de fin')
    active = models.BooleanField('Active', default=True)
    products = models.ManyToManyField(Product, related_name='promotions', blank=True, verbose_name='Produits concernés')
    min_purchase = models.DecimalField('Achat minimum (FCFA)', max_digits=10, decimal_places=2, default=0)
    applies_to_all = models.BooleanField('Appliquer à tous les produits', default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date']
        verbose_name = 'Promotion'
        verbose_name_plural = 'Promotions'

    def __str__(self):
        if self.discount_type == 'percentage':
            value = f'{self.discount_value}%'
        else:
            value = f'{self.discount_value} FCFA'
        return f'{self.name} ({value})'

    @property
    def is_active(self):
        today = date.today()
        return self.active and self.start_date <= today <= self.end_date

    def apply_discount(self, price):
        if self.discount_type == 'percentage':
            return price * (1 - self.discount_value / 100)
        return max(price - self.discount_value, 0)


class CustomerOrder(models.Model):
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('confirmed', 'Confirmée'),
        ('ready', 'Prête'),
        ('delivered', 'Livrée'),
        ('cancelled', 'Annulée'),
    ]

    customer = models.ForeignKey(Customer, related_name='orders', null=True, blank=True, on_delete=models.SET_NULL)
    customer_name = models.CharField('Nom client', max_length=200, blank=True, default='')
    customer_phone = models.CharField('Téléphone', max_length=30, blank=True, default='')
    date = models.DateField('Date de commande', default=date.today)
    pickup_date = models.DateField('Date de retrait prévue', null=True, blank=True)
    status = models.CharField('Statut', max_length=10, choices=STATUS_CHOICES, default='pending')
    total = models.DecimalField('Total (FCFA)', max_digits=10, decimal_places=2, default=0)
    deposit = models.DecimalField('Acompte (FCFA)', max_digits=10, decimal_places=2, default=0)
    notes = models.TextField('Notes', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = 'Commande client'
        verbose_name_plural = 'Commandes clients'

    def __str__(self):
        return f'Commande #{self.id} - {self.customer_name or "Client"} ({self.get_status_display()})'

    @property
    def balance_due(self):
        return self.total - self.deposit


class CustomerOrderItem(models.Model):
    order = models.ForeignKey(CustomerOrder, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.DecimalField('Quantité', max_digits=10, decimal_places=2)
    price = models.DecimalField('Prix unitaire (FCFA)', max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'Ligne de commande client'
        verbose_name_plural = 'Lignes de commande client'

    def __str__(self):
        return f'{self.product.name} x {self.quantity}'

    @property
    def subtotal(self):
        return self.quantity * self.price


class ProductReturn(models.Model):
    RETURN_REASON_CHOICES = [
        ('defective', 'Produit défectueux'),
        ('expired', 'Périmé'),
        ('wrong', 'Produit erroné'),
        ('customer_request', 'Demande client'),
        ('exchange', 'Échange'),
        ('other', 'Autre'),
    ]

    RETURN_STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('approved', 'Approuvé'),
        ('rejected', 'Rejeté'),
    ]

    sale = models.ForeignKey(Sale, related_name='returns', on_delete=models.CASCADE, verbose_name='Vente')
    date = models.DateField('Date du retour', default=date.today)
    reason = models.CharField('Raison', max_length=20, choices=RETURN_REASON_CHOICES, default='customer_request')
    status = models.CharField('Statut', max_length=10, choices=RETURN_STATUS_CHOICES, default='pending')
    refund_amount = models.DecimalField('Montant remboursé (FCFA)', max_digits=10, decimal_places=2, default=0)
    notes = models.TextField('Notes', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = 'Retour / Échange'
        verbose_name_plural = 'Retours / Échanges'

    def __str__(self):
        return f'Retour #{self.id} - Vente #{self.sale_id} ({self.get_reason_display()})'


class ProductReturnItem(models.Model):
    product_return = models.ForeignKey(ProductReturn, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Produit')
    quantity = models.DecimalField('Quantité retournée', max_digits=10, decimal_places=2)
    refund_amount = models.DecimalField('Montant remboursé (FCFA)', max_digits=10, decimal_places=2, default=0)

    class Meta:
        verbose_name = 'Ligne de retour'
        verbose_name_plural = 'Lignes de retour'

    def __str__(self):
        return f'{self.product.name} x {self.quantity}'


class StockLoss(models.Model):
    REASON_CHOICES = [
        ('expired', 'Périmé'),
        ('damaged', 'Endommagé'),
        ('stolen', 'Vol'),
        ('other', 'Autre'),
    ]
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Produit')
    quantity = models.DecimalField('Quantité perdue', max_digits=10, decimal_places=2)
    loss_amount = models.DecimalField('Montant de la perte (FCFA)', max_digits=10, decimal_places=2, default=0)
    date = models.DateField('Date', default=date.today)
    reason = models.CharField('Raison', max_length=20, choices=REASON_CHOICES, default='expired')
    notes = models.TextField('Notes', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = 'Perte de stock'
        verbose_name_plural = 'Pertes de stock'

    def __str__(self):
        return f'{self.product.name} - {self.quantity} ({self.get_reason_display()})'

    def save(self, *args, **kwargs):
        if not self.loss_amount:
            self.loss_amount = self.quantity * (self.product.cost_price or 0)
        super().save(*args, **kwargs)


class SupplierReturn(models.Model):
    REASON_CHOICES = [
        ('defective', 'Produit défectueux'),
        ('expired', 'Périmé'),
        ('wrong', 'Produit erroné'),
        ('overstock', 'Surstock'),
        ('other', 'Autre'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Brouillon'),
        ('sent', 'Retourné au fournisseur'),
        ('credited', 'Avoir reçu'),
        ('cancelled', 'Annulé'),
    ]

    supplier = models.ForeignKey(Supplier, related_name='returns', on_delete=models.CASCADE, verbose_name='Fournisseur')
    date = models.DateField('Date du retour', default=date.today)
    reason = models.CharField('Raison', max_length=20, choices=REASON_CHOICES, default='defective')
    status = models.CharField('Statut', max_length=10, choices=STATUS_CHOICES, default='draft')
    total = models.DecimalField('Total (FCFA)', max_digits=12, decimal_places=2, default=0)
    notes = models.TextField('Notes', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = 'Retour fournisseur'
        verbose_name_plural = 'Retours fournisseurs'

    def __str__(self):
        return f'Retour #{self.id} - {self.supplier.name} ({self.get_status_display()})'

    def update_total(self):
        self.total = sum(item.subtotal for item in self.items.all())
        self.save(update_fields=['total'])


class SupplierReturnItem(models.Model):
    supplier_return = models.ForeignKey(SupplierReturn, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Produit')
    quantity = models.DecimalField('Quantité retournée', max_digits=10, decimal_places=2)
    unit_cost = models.DecimalField('Prix d\'achat unitaire (FCFA)', max_digits=10, decimal_places=2, default=0)
    reason = models.CharField('Raison', max_length=20, choices=SupplierReturn.REASON_CHOICES, default='defective')

    class Meta:
        verbose_name = 'Ligne de retour fournisseur'
        verbose_name_plural = 'Lignes de retour fournisseur'

    def __str__(self):
        return f'{self.product.name} x {self.quantity}'

    @property
    def subtotal(self):
        return self.quantity * self.unit_cost


class BankAccount(models.Model):
    name = models.CharField('Nom du compte', max_length=200)
    account_number = models.CharField('Numéro de compte', max_length=50, blank=True, default='')
    bank_name = models.CharField('Banque', max_length=200, blank=True, default='')
    balance = models.DecimalField('Solde (FCFA)', max_digits=14, decimal_places=2, default=0)
    notes = models.TextField('Notes', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Compte bancaire'
        verbose_name_plural = 'Comptes bancaires'

    def __str__(self):
        return f'{self.name} - {self.balance} FCFA'


class BankTransaction(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ('deposit', 'Dépôt'),
        ('withdrawal', 'Retrait'),
        ('transfer_in', 'Virement reçu'),
        ('transfer_out', 'Virement émis'),
    ]

    account = models.ForeignKey(BankAccount, related_name='transactions', on_delete=models.CASCADE, verbose_name='Compte')
    transaction_type = models.CharField('Type', max_length=15, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField('Montant (FCFA)', max_digits=14, decimal_places=2)
    date = models.DateField('Date', default=date.today)
    description = models.CharField('Description', max_length=250, blank=True, default='')
    reference = models.CharField('Référence', max_length=100, blank=True, default='')
    notes = models.TextField('Notes', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = 'Opération bancaire'
        verbose_name_plural = 'Opérations bancaires'

    def __str__(self):
        return f'{self.get_transaction_type_display()} - {self.amount} FCFA - {self.account.name}'

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            self._update_account_balance()

    def delete(self, *args, **kwargs):
        self._reverse_balance()
        super().delete(*args, **kwargs)

    def _update_account_balance(self):
        if self.transaction_type in ('deposit', 'transfer_in'):
            self.account.balance += self.amount
        else:
            self.account.balance -= self.amount
        self.account.save(update_fields=['balance'])

    def _reverse_balance(self):
        if self.transaction_type in ('deposit', 'transfer_in'):
            self.account.balance -= self.amount
        else:
            self.account.balance += self.amount
        self.account.save(update_fields=['balance'])


class LoyaltyProgram(models.Model):
    name = models.CharField('Nom du programme', max_length=200, default='Fidélité')
    points_per_purchase = models.DecimalField('Points par 1000 FCFA d\'achat', max_digits=5, decimal_places=2, default=10)
    points_value = models.DecimalField('Valeur de 1 point (FCFA)', max_digits=5, decimal_places=2, default=1)
    min_points_to_redeem = models.DecimalField('Points minimum pour échanger', max_digits=8, decimal_places=2, default=100)
    active = models.BooleanField('Actif', default=True)

    class Meta:
        verbose_name = 'Programme de fidélité'
        verbose_name_plural = 'Programmes de fidélité'

    def __str__(self):
        return f'{self.name} ({self.points_per_purchase} pts/1000F)'

    @classmethod
    def load(cls):
        program, _ = cls.objects.get_or_create(pk=1)
        return program


class LoyaltyTransaction(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ('earn', 'Gain'),
        ('burn', 'Échange'),
        ('bonus', 'Bonus'),
        ('expired', 'Expiré'),
    ]

    customer = models.ForeignKey(Customer, related_name='loyalty_transactions', on_delete=models.CASCADE)
    points = models.DecimalField('Points', max_digits=10, decimal_places=2)
    transaction_type = models.CharField('Type', max_length=10, choices=TRANSACTION_TYPE_CHOICES)
    sale = models.ForeignKey(Sale, null=True, blank=True, on_delete=models.SET_NULL)
    description = models.CharField('Description', max_length=250, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Transaction de fidélité'
        verbose_name_plural = 'Transactions de fidélité'

    def __str__(self):
        return f'{self.customer.name} {self.get_transaction_type_display()} {self.points} pts'

    @classmethod
    def get_balance(cls, customer):
        earned = cls.objects.filter(customer=customer, transaction_type__in=['earn', 'bonus']).aggregate(
            total=Sum('points')
        )['total'] or 0
        used = cls.objects.filter(customer=customer, transaction_type__in=['burn', 'expired']).aggregate(
            total=Sum('points')
        )['total'] or 0
        return earned - used


class SolarComponent(models.Model):
    name = models.CharField('Nom', max_length=200)
    category = models.CharField('Catégorie', max_length=50, choices=[
        ('panneau', 'Panneau solaire'),
        ('batterie', 'Batterie'),
        ('onduleur', 'Onduleur/Convertisseur'),
        ('structure', 'Structure & Support'),
        ('cable', 'Câble & Connectique'),
        ('tableau', 'Tableau électrique'),
        ('main_oeuvre', 'Main-d\'œuvre'),
        ('divers', 'Divers'),
    ], default='divers')
    unit_price = models.DecimalField('Prix vente (FCFA)', max_digits=12, decimal_places=2, default=0)
    cost_price = models.DecimalField('Prix revient (FCFA)', max_digits=12, decimal_places=2, default=0)
    stock = models.DecimalField('Stock', max_digits=10, decimal_places=2, default=0)
    notes = models.TextField('Notes', blank=True)

    class Meta:
        ordering = ['category', 'name']
        verbose_name = 'Composant solaire'
        verbose_name_plural = 'Composants solaires'

    def __str__(self):
        return f'{self.name} ({self.unit_price} F)'


class SolarProject(models.Model):
    STATUS_CHOICES = [
        ('devis', 'Devis'),
        ('confirmé', 'Confirmé'),
        ('installé', 'Installé'),
        ('terminé', 'Terminé'),
        ('perdu', 'Marché perdu'),
        ('annulé', 'Annulé'),
    ]

    SYSTEM_CHOICES = [
        ('on_grid', 'On-grid (Raccordé réseau)'),
        ('off_grid', 'Off-grid (Autonome)'),
        ('hybrid', 'Hybride'),
    ]

    client_name = models.CharField('Nom du client', max_length=200)
    client_phone = models.CharField('Téléphone', max_length=30, blank=True, default='')
    client_address = models.CharField('Adresse', max_length=300, blank=True, default='')
    date = models.DateField('Date', default=date.today)
    status = models.CharField('Statut', max_length=10, choices=STATUS_CHOICES, default='devis')
    system_type = models.CharField('Type de système', max_length=10, choices=SYSTEM_CHOICES, default='off_grid')
    capacity_kw = models.DecimalField('Capacité (kWc)', max_digits=8, decimal_places=2, null=True, blank=True)
    panel_count = models.PositiveIntegerField('Nombre de panneaux', default=0)
    battery_count = models.PositiveIntegerField('Nombre de batteries', default=0)
    inverter_count = models.PositiveIntegerField('Nombre d\'onduleurs', default=0)
    total_cost = models.DecimalField('Coût total (FCFA)', max_digits=12, decimal_places=2, default=0)
    total_price = models.DecimalField('Prix total (FCFA)', max_digits=12, decimal_places=2, default=0)
    deposit = models.DecimalField('Acompte (FCFA)', max_digits=12, decimal_places=2, default=0)
    actual_profit = models.DecimalField('Gain réel (FCFA)', max_digits=12, decimal_places=2, null=True, blank=True)
    won_date = models.DateField('Date de réalisation', null=True, blank=True)
    notes = models.TextField('Notes', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = 'Projet solaire'
        verbose_name_plural = 'Projets solaires'

    def __str__(self):
        return f'Solaire #{self.id} - {self.client_name} ({self.get_status_display()})'

    @property
    def balance_due(self):
        return self.total_price - self.deposit

    @property
    def profit(self):
        return self.total_price - self.total_cost

    def update_totals(self):
        items = self.items.all()
        self.total_cost = sum(i.total_cost for i in items)
        self.total_price = sum(i.total for i in items)
        self.save(update_fields=['total_cost', 'total_price'])


class SolarProjectItem(models.Model):
    project = models.ForeignKey(SolarProject, related_name='items', on_delete=models.CASCADE)
    component = models.ForeignKey(SolarComponent, null=True, blank=True, on_delete=models.SET_NULL, verbose_name='Composant')
    designation = models.CharField('Désignation', max_length=300)
    quantity = models.DecimalField('Quantité', max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField('Prix unitaire (FCFA)', max_digits=12, decimal_places=2, default=0)
    cost_price = models.DecimalField('Prix de revient (FCFA)', max_digits=12, decimal_places=2, default=0)

    class Meta:
        verbose_name = 'Ligne de devis solaire'
        verbose_name_plural = 'Lignes de devis solaire'

    def __str__(self):
        return f'{self.designation} x {self.quantity}'

    @property
    def total(self):
        return self.quantity * self.unit_price

    @property
    def total_cost(self):
        return self.quantity * self.cost_price


class GiftCard(models.Model):
    code = models.CharField('Code', max_length=20, unique=True)
    initial_balance = models.DecimalField('Solde initial', max_digits=10, decimal_places=2)
    balance = models.DecimalField('Solde restant', max_digits=10, decimal_places=2)
    customer = models.ForeignKey(Customer, null=True, blank=True, on_delete=models.SET_NULL, verbose_name='Client')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateField("Date d'expiration", null=True, blank=True)
    active = models.BooleanField('Active', default=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Carte cadeau'
        verbose_name_plural = 'Cartes cadeaux'

    def __str__(self):
        return f'{self.code} — {self.balance:,.0f} FCFA'

    @property
    def is_expired(self):
        return self.expires_at and self.expires_at < date.today()

    @property
    def is_usable(self):
        return self.active and not self.is_expired and self.balance > 0


class GiftCardUsage(models.Model):
    giftcard = models.ForeignKey(GiftCard, on_delete=models.CASCADE, related_name='usages')
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE)
    amount = models.DecimalField('Montant utilisé', max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Utilisation carte cadeau'
        verbose_name_plural = 'Utilisations cartes cadeaux'


class ActivityLog(models.Model):
    ACTION_CHOICES = [
        ('created', 'Création'),
        ('updated', 'Modification'),
        ('deleted', 'Suppression'),
        ('paid', 'Paiement'),
        ('delivered', 'Livré'),
    ]
    user = models.CharField(max_length=100)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=50)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    object_repr = models.CharField(max_length=200)
    details = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Journal activité'
        verbose_name_plural = "Journal d'activités"


class Recipe(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='recipe', verbose_name='Produit composite')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Recette / Produit composite'
        verbose_name_plural = 'Recettes / Produits composites'

    def __str__(self):
        return f'Recette: {self.product.name}'

    @property
    def total_ingredient_cost(self):
        return sum(item.total_cost for item in self.ingredients.all())

    @property
    def margin(self):
        cost = self.total_ingredient_cost
        if not cost or not self.product.price:
            return 0
        return float((self.product.price - cost) / cost) * 100

    @property
    def gross_profit(self):
        cost = self.total_ingredient_cost
        price = self.product.price or 0
        return price - cost


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='ingredients', verbose_name='Recette')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='used_in_recipes', verbose_name='Ingrédient')
    quantity = models.DecimalField('Quantité', max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'Ingrédient de recette'
        verbose_name_plural = 'Ingrédients des recettes'

    def __str__(self):
        return f'{self.quantity} x {self.product.name}'

    @property
    def total_cost(self):
        cost = self.product.cost_price
        if cost is None or not self.quantity:
            return Decimal('0')
        return self.quantity * cost


class Employee(models.Model):
    ROLE_CHOICES = [
        ('cashier', 'Caissier(ère)'),
        ('manager', 'Gérant(e)'),
        ('stock_keeper', 'Magasinier(ère)'),
        ('sales', 'Vendeur(se)'),
        ('cleaner', 'Agent d\'entretien'),
        ('other', 'Autre'),
    ]

    first_name = models.CharField('Prénom', max_length=100)
    last_name = models.CharField('Nom', max_length=100)
    phone = models.CharField('Téléphone', max_length=30, blank=True)
    email = models.EmailField('Email', blank=True)
    role = models.CharField('Poste', max_length=20, choices=ROLE_CHOICES, default='cashier')
    salary = models.DecimalField('Salaire (FCFA)', max_digits=12, decimal_places=2, default=0)
    hire_date = models.DateField("Date d'embauche", default=date.today)
    is_active = models.BooleanField('Actif', default=True)
    notes = models.TextField('Notes', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['last_name', 'first_name']
        verbose_name = 'Employé'
        verbose_name_plural = 'Employés'

    def __str__(self):
        return f'{self.first_name} {self.last_name} ({self.get_role_display()})'


class Attendance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendance', verbose_name='Employé')
    clock_in = models.DateTimeField('Arrivée', auto_now_add=True)
    clock_out = models.DateTimeField('Départ', null=True, blank=True)

    class Meta:
        ordering = ['-clock_in']
        verbose_name = 'Pointage'
        verbose_name_plural = 'Pointages'

    def __str__(self):
        out = self.clock_out.strftime('%H:%M') if self.clock_out else 'En cours'
        return f'{self.employee} — {self.clock_in:%d/%m/%Y} {self.clock_in:%H:%M} → {out}'

    @property
    def duration(self):
        if not self.clock_out:
            return None
        delta = self.clock_out - self.clock_in
        hours = delta.total_seconds() / 3600
        return round(hours, 1)


class CoiffureClient(models.Model):
    name = models.CharField('Nom', max_length=200)
    phone = models.CharField('Téléphone', max_length=30)
    notes = models.TextField('Notes', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Client coiffure'
        verbose_name_plural = 'Clients coiffure'

    def __str__(self):
        return f'{self.name} — {self.phone}'
