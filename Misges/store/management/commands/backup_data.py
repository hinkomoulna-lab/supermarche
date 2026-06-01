import gzip
import hashlib
import base64
import os
from io import StringIO
from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Sauvegarde toutes les données dans un fichier .json.gz'

    def add_arguments(self, parser):
        parser.add_argument('--output-dir', default=None, help='Répertoire de destination')
        parser.add_argument('--password', default=None, help='Mot de passe pour chiffrer la sauvegarde')

    def handle(self, *args, **options):
        output_dir = options['output_dir'] or os.path.join(settings.BASE_DIR, 'backups')
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        password = options.get('password')

        buf = StringIO()
        call_command('dumpdata', 'store', indent=2, stdout=buf, exclude=['contenttypes', 'auth.permission'])
        raw = buf.getvalue().encode('utf-8')
        compressed = gzip.compress(raw)

        if password:
            key = hashlib.sha256(password.encode()).digest()
            encrypted = bytearray()
            for i, b in enumerate(compressed):
                encrypted.append(b ^ key[i % len(key)])
            compressed = base64.b64encode(bytes(encrypted))
            filename = f'sauvegarde_{timestamp}.bak'
        else:
            filename = f'sauvegarde_{timestamp}.json.gz'

        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'wb') as f:
            f.write(compressed)

        self.stdout.write(self.style.SUCCESS(f'Sauvegarde créée : {filepath}'))
        size = os.path.getsize(filepath)
        self.stdout.write(f'Taille : {size / 1024:.1f} Ko')