import os, sys, subprocess, webbrowser, threading, time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MISGES_DIR = os.path.join(BASE_DIR, 'Misges')
os.chdir(MISGES_DIR)
sys.path.insert(0, MISGES_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'supermarket.settings')


def run_server():
    from django.core.management import execute_from_command_line
    sys.argv = ['manage.py', 'runserver', '0.0.0.0:8000', '--noreload']
    execute_from_command_line(sys.argv)


t = threading.Thread(target=run_server, daemon=True)
t.start()

time.sleep(2)
webbrowser.open('http://127.0.0.1:8000')

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    pass
