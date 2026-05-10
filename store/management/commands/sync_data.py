import base64
import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from store.models import Product


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


class Command(BaseCommand):
    help = "Synchronise toutes les données depuis fixtures/full_data.json"

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Forcer l\'import même si des données existent')

    def handle(self, *args, **options):
        if Product.objects.count() > 0 and not options['force']:
            self.stdout.write('Des données existent déjà. Utilise --force pour réimporter.')
            return

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

        self.stdout.write(f'Import de {len(data)} enregistrements...')
        from django.core import serializers
        try:
            for obj in serializers.deserialize('json', json.dumps(data)):
                obj.save()
            self.stdout.write(self.style.SUCCESS(f'{len(data)} enregistrements importés'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erreur import : {e}'))
