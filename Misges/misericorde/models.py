from django.db import models

class Service(models.Model):
    ICON_CHOICES = [
        ('bi-heart', 'Cœur'),
        ('bi-people', 'Personnes'),
        ('bi-cup-hot', 'Repas'),
        ('bi-book', 'Livre'),
        ('bi-house-door', 'Maison'),
        ('bi-church', 'Église'),
        ('bi-hand-index-thumb', 'Aide'),
        ('bi-music-note', 'Musique'),
    ]
    title = models.CharField('Titre', max_length=200)
    description = models.TextField('Description')
    icon = models.CharField('Icône', max_length=50, choices=ICON_CHOICES, default='bi-heart')
    order = models.PositiveIntegerField('Ordre', default=0)

    class Meta:
        ordering = ['order']
        verbose_name = 'Service'
        verbose_name_plural = 'Services'

    def __str__(self):
        return self.title


class Schedule(models.Model):
    DAY_CHOICES = [
        ('lundi', 'Lundi'), ('mardi', 'Mardi'), ('mercredi', 'Mercredi'),
        ('jeudi', 'Jeudi'), ('vendredi', 'Vendredi'), ('samedi', 'Samedi'),
        ('dimanche', 'Dimanche'),
    ]
    day = models.CharField('Jour', max_length=10, choices=DAY_CHOICES, unique=True)
    morning = models.CharField('Matin', max_length=100, blank=True, default='')
    afternoon = models.CharField('Après-midi', max_length=100, blank=True, default='')
    closed = models.BooleanField('Fermé', default=False)

    class Meta:
        verbose_name = 'Horaire'
        verbose_name_plural = 'Horaires'

    def __str__(self):
        return self.get_day_display()


class ContactMessage(models.Model):
    name = models.CharField('Nom', max_length=200)
    email = models.EmailField('Email')
    phone = models.CharField('Téléphone', max_length=30, blank=True)
    subject = models.CharField('Sujet', max_length=300)
    message = models.TextField('Message')
    created_at = models.DateTimeField('Date', auto_now_add=True)
    read = models.BooleanField('Lu', default=False)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Message de contact'
        verbose_name_plural = 'Messages de contact'

    def __str__(self):
        return f'{self.name} — {self.subject}'


class SiteContent(models.Model):
    KEY_CHOICES = [
        ('hero_title', 'Titre hero'),
        ('hero_subtitle', 'Sous-titre hero'),
        ('about_title', 'Titre À propos'),
        ('about_text', 'Texte À propos'),
        ('services_intro', 'Introduction services'),
        ('contact_address', 'Adresse'),
        ('contact_phone', 'Téléphone'),
        ('contact_email', 'Email'),
    ]
    key = models.CharField('Clé', max_length=50, unique=True, choices=KEY_CHOICES)
    value = models.TextField('Valeur')

    class Meta:
        verbose_name = 'Contenu du site'
        verbose_name_plural = 'Contenus du site'

    def __str__(self):
        return self.get_key_display()
