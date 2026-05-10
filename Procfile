release: python manage.py migrate --noinput && python manage.py sync_data && python manage.py load_initial_data && python manage.py ensure_admin
web: python manage.py collectstatic --noinput && gunicorn supermarket.wsgi:application
