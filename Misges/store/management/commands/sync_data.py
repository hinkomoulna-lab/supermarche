import base64
import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core import serializers
from store.models import Product, StoreSettings, Category


def decode_media(media_files):
    if not media_files:
        return
    for file_path, info in media_files.items():
        dest = os.path.join(settings.MEDIA_ROOT, file_path)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        try:
            content = base64.b64decode(info['content'])
            with open(dest, 'wb') as f:
                f.write(content)
        except Exception as e:
            print(f'  Erreur média {file_path}: {e}')


always_models = {'store.storesettings', 'store.category'}


class Command(BaseCommand):
    help = "Synchronise les données depuis fixtures/full_data.json"

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Forcer l\'import complet')

    def handle(self, *args, **options):
        json_path = os.path.join(settings.BASE_DIR, 'fixtures', 'full_data.json')
        if not os.path.exists(json_path):
            self.stdout.write(self.style.ERROR(f'Fichier introuvable : {json_path}'))
            return

        with open(json_path, 'r', encoding='utf-8') as f:
            payload = json.load(f)

        data = payload.get('data', [])
        media_files = payload.get('_media_files', {})

        self.stdout.write(f'Restauration de {len(media_files)} fichiers média...')
        decode_media(media_files)

        if Product.objects.count() > 0 and not options.get('force'):
            always = [d for d in data if d.get('model') in always_models]
            if always:
                self.stdout.write(f'Import des paramètres et catégories ({len(always)})...')
                for obj in serializers.deserialize('json', json.dumps(always)):
                    obj.save()
            self.stdout.write('Produits existants, import ignoré (utilise --force pour réimporter tout)')
            return

        self.stdout.write(f'Import de {len(data)} enregistrements...')
        try:
            for obj in serializers.deserialize('json', json.dumps(data)):
                obj.save()
            self.stdout.write(self.style.SUCCESS(f'{len(data)} enregistrements importés'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erreur import : {e}'))
