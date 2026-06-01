#!/usr/bin/env bash
set -euo pipefail

# ──────────────────────────────────────────────
# Déploiement automatique — Supermarché Django
# Testé sur Ubuntu 22.04 / 24.04
# ──────────────────────────────────────────────

DOMAIN="${1:-ton-domaine.com}"
APP_DIR="/home/django/supermarche"
USER="django"

if [ "$DOMAIN" = "ton-domaine.com" ]; then
    echo "⚠️  Remplace ton-domaine.com par ton vrai domaine."
    echo "Usage: bash deploy.sh mon-domaine.com"
    exit 1
fi

echo "→ Mise à jour du système…"
apt update && apt upgrade -y

echo "→ Installation des dépendances…"
apt install -y python3 python3-pip python3-venv python3-dev
apt install -y nginx certbot python3-certbot-nginx
apt install -y git postgresql postgresql-client libpq-dev
apt install -y redis-server  # optionnel pour cache/sessions

echo "→ Création de l'utilisateur $USER…"
id -u $USER &>/dev/null || useradd -m -s /bin/bash $USER
usermod -a -G www-data $USER

echo "→ Création des dossiers…"
mkdir -p $APP_DIR
mkdir -p /var/log/gunicorn
mkdir -p /var/log/nginx
chown -R $USER:www-data $APP_DIR /var/log/gunicorn

echo "→ Cloner / copier le projet…"
# Si tu déposes les fichiers manuellement via SCP/rsync, voici la structure attendue :
# $APP_DIR/
# ├── Misges/        ← tout le code Django
# ├── deploy/        ← ce dossier
# ├── .env           ← variables d'environnement
# └── venv/          ← virtualenv
#
# Sinon clone depuis git :
# git clone https://github.com/ton-compte/supermarche.git $APP_DIR

echo "→ Configuration de l'environnement virtuel…"
python3 -m venv $APP_DIR/venv
source $APP_DIR/venv/bin/activate
pip install --upgrade pip
pip install gunicorn psycopg2-binary dj-database-url

if [ -f "$APP_DIR/Misges/requirements.txt" ]; then
    pip install -r $APP_DIR/Misges/requirements.txt
fi

echo "→ Variables d'environnement…"
if [ ! -f "$APP_DIR/.env" ]; then
    cp $APP_DIR/deploy/.env.example $APP_DIR/.env
    echo "⚠️  Édite $APP_DIR/.env avant de continuer !"
    echo "   nano $APP_DIR/.env"
    echo "   Puis relance ce script."
    exit 1
fi

set -a; source $APP_DIR/.env; set +a

echo "→ Collecte des fichiers statiques…"
cd $APP_DIR/Misges
$APP_DIR/venv/bin/python manage.py collectstatic --noinput

echo "→ Migrations…"
$APP_DIR/venv/bin/python manage.py migrate --noinput

echo "→ Configuration Nginx…"
cp $APP_DIR/deploy/nginx.conf /etc/nginx/sites-available/supermarche
sed -i "s/ton-domaine.com/$DOMAIN/g" /etc/nginx/sites-available/supermarche
ln -sf /etc/nginx/sites-available/supermarche /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

echo "→ Configuration Gunicorn (systemd)…"
cp $APP_DIR/deploy/gunicorn.service /etc/systemd/system/gunicorn.service
systemctl daemon-reload
systemctl enable gunicorn
systemctl restart gunicorn

echo "→ SSL avec Let's Encrypt…"
certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos -m admin@$DOMAIN || true

echo "→ Redémarrage final…"
systemctl restart nginx gunicorn

echo ""
echo "✅ Déploiement terminé !"
echo "   Site : https://$DOMAIN"
echo "   Admin : https://$DOMAIN/admin/"
echo "   Commandes QR : https://$DOMAIN/commande/"
echo ""
echo "📌 Prochaines étapes :"
echo "   1. Crée un superuser : $APP_DIR/venv/bin/python $APP_DIR/Misges/manage.py createsuperuser"
echo "   2. Vérifie les logs : journalctl -u gunicorn -f"
echo "   3. Active le pare-feu : ufw allow 'Nginx Full'"
