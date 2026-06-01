import os
from django.apps import AppConfig
from django.db.models.signals import post_migrate

def create_default_admin(sender, **kwargs):
    admin_user = os.getenv('DJANGO_SUPERUSER_USERNAME', '').strip()
    admin_pass = os.getenv('DJANGO_SUPERUSER_PASSWORD', '').strip()
    if admin_user and admin_pass:
        from django.contrib.auth.models import User
        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser(admin_user, '', admin_pass)

class StoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'store'

    def ready(self):
        post_migrate.connect(create_default_admin, sender=self)
