 Déploiement gratuit sur PythonAnywhere

Étape 1 : Crée un compte
 1. Va sur https://www.pythonanywhere.com
 2. Clique "Create a Beginner Account" (gratuit)
 3. Choisis un nom d'utilisateur (ex: tonmagasin)
 4. Ton site sera → https://tonmagasin.pythonanywhere.com

Étape 2 : Ouvre une console Bash
 1. Une fois connecté, clique "Consoles" → "Bash"

Étape 3 : Clone le projet depuis GitHub
```bash
# Si tu as un dépôt GitHub :
git clone https://github.com/ton-compte/supermarche.git

# Sinon, tu peux uploader les fichiers via l'onglet "Files"
```

Étape 4 : Crée l'environnement virtuel
```bash
cd supermarche/Misges
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Étape 5 : Configure la base de données
```bash
# SQLite (recommandé pour commencer) :
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

Étape 6 : Configure le Web App
 1. Va dans l'onglet "Web"
 2. Clique "Add a new web app"
 3. Choisis "Manual configuration" → "Python 3.12"
 4. Dans "Code":
    - Source code: /home/tonmagasin/supermarche/Misges
    - Working directory: /home/tonmagasin/supermarche/Misges
    - WSGI configuration file: Clique sur le lien pour l'éditer

 5. Dans le fichier WSGI, remplace tout par :
```python
import os
import sys

path = '/home/tonmagasin/supermarche/Misges'
if path not in sys.path:
    sys.path.insert(0, path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'supermarket.settings'
os.environ['DJANGO_DEBUG'] = '0'
os.environ['DJANGO_ALLOWED_HOSTS'] = 'tonmagasin.pythonanywhere.com'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

 6. **Static files**:
    - URL: /static/
    - Path: /home/tonmagasin/supermarche/Misges/staticfiles

 7. **Media files** (optionnel):
    - URL: /media/
    - Path: /home/tonmagasin/supermarche/Misges/media

 8. Clique "Reload" (le bouton vert en haut)

Étape 7 : Teste
 - Ouvre https://tonmagasin.pythonanywhere.com
 - QR : https://tonmagasin.pythonanywhere.com/commande/staff/qr/
 - Catalogue : https://tonmagasin.pythonanywhere.com/commande/

⚠️ Important pour le free tier
 - Le site s'éteint après inactivité (se réveille au premier visiteur)
 - 512 Mo de stockage (suffisant pour SQLite)
 - Pas de nom de domaine personnalisé
 - Pas de connexion SSH

Pour générer le QR, ouvre la page QR et scanne depuis ton téléphone :
https://tonmagasin.pythonanywhere.com/commande/staff/qr/
