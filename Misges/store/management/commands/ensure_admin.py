from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
import os

class Command(BaseCommand):
    help = 'Crée/met à jour un superutilisateur'

    def handle(self, *args, **options):
        username = os.getenv('DJANGO_SUPERUSER_USERNAME', 'admin')
        password = os.getenv('DJANGO_SUPERUSER_PASSWORD', 'admin123')
        email = os.getenv('DJANGO_SUPERUSER_EMAIL', 'admin@admin.com')

        if User.objects.filter(username=username).exists():
            u = User.objects.get(username=username)
            u.set_password(password)
            u.is_superuser = True
            u.is_staff = True
            u.save()
            self.stdout.write(f'Mot de passe mis à jour pour {username}')
        else:
            User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(f'Superutilisateur {username} créé')
