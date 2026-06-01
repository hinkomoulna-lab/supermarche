import base64
import json
import os
from io import StringIO
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.conf import settings


MEDIA_FIELDS = {
    'store.product': ['image'],
    'store.storesettings': ['logo', 'background_image', 'invoice_watermark', 'signature'],
}


class Command(BaseCommand):
    help = "Exporte toutes les données + fichiers média en JSON"

    def handle(self, *args, **options):
        buffer = StringIO()
        call_command('dumpdata', 'store', indent=2, stdout=buffer,
                     exclude=['contenttypes', 'auth.permission', 'sessions', 'admin'])
        data = json.loads(buffer.getvalue())

        media_files = {}
        for entry in data:
            model = entry.get('model')
            fields = entry.get('fields', {})
            file_fields = MEDIA_FIELDS.get(model, [])
            for field in file_fields:
                file_path = fields.get(field)
                if file_path:
                    full_path = os.path.join(settings.MEDIA_ROOT, file_path)
                    if os.path.exists(full_path):
                        with open(full_path, 'rb') as f:
                            encoded = base64.b64encode(f.read()).decode('utf-8')
                            ext = os.path.splitext(file_path)[1].lstrip('.')
                            media_files[file_path] = {
                                'content': encoded,
                                'ext': ext,
                            }
                            self.stdout.write(f'  Media: {file_path} ({len(encoded)//1024} KB)')

        output = {
            'data': data,
            '_media_files': media_files,
        }

        output_path = os.path.join(settings.BASE_DIR, 'fixtures', 'full_data.json')
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        total_items = len(data)
        total_media = len(media_files)
        self.stdout.write(self.style.SUCCESS(
            f'Export terminé : {total_items} enregistrements, {total_media} fichiers média'
        ))
