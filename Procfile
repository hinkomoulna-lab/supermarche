release: python manage.py migrate --noinput && python manage.py load_initial_data
web: python manage.py collectstatic --noinput && gunicorn supermarket.wsgi:application
