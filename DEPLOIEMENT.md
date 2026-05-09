# Déploiement Internet

Objectif : accéder à l'application depuis ton téléphone même en voyage.

## Ce qui est déjà préparé

- Configuration par variables d'environnement dans `supermarket/settings.py`
- Page de connexion Django prête
- Protection optionnelle de toute l'application avec `REQUIRE_LOGIN=1`
- Dépendances de production dans `requirements.txt`
- Fichier `.python-version`
- `Procfile` pour lancer migrations, fichiers statiques et serveur Gunicorn

## Variables à mettre chez l'hébergeur

```text
DJANGO_SECRET_KEY=une-longue-cle-secrete
DJANGO_DEBUG=0
DJANGO_ALLOWED_HOSTS=ton-domaine.com,ton-app.onrender.com
REQUIRE_LOGIN=1
DATABASE_URL=postgres://...
OPENAI_API_KEY=ta-cle-api-openai
OPENAI_MODEL=gpt-5.2
```

## Étapes recommandées sur Render

1. Créer un compte Render.
2. Mettre ce projet sur GitHub.
3. Créer une base PostgreSQL.
4. Créer un Web Service Python depuis le dépôt GitHub.
5. Ajouter les variables d'environnement ci-dessus.
6. Déployer.
7. Créer un utilisateur :

```powershell
python manage.py createsuperuser
```

Après ça, tu pourras ouvrir l'adresse publique depuis ton téléphone partout.
