from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.views.static import serve
from store.forms import LoginForm
from django.http import FileResponse
from django.contrib.staticfiles.views import serve as static_serve
import os

sw_path = os.path.join(settings.STATICFILES_DIRS[0], 'pwa', 'sw.js')

def serve_sw(request):
    return FileResponse(open(sw_path, 'rb'), content_type='application/javascript')

def serve_static(request, path):
    return static_serve(request, path, insecure=True)

urlpatterns = [
    path('sw.js', serve_sw, name='service_worker'),
    path('admin/', admin.site.urls),
    path('connexion/', auth_views.LoginView.as_view(
        template_name='registration/login.html',
        authentication_form=LoginForm,
    ), name='login'),
    path('deconnexion/', auth_views.LogoutView.as_view(), name='logout'),
    path('commande/', include('commande.urls')),
    path('misericorde/', include('misericorde.urls')),
    path('', include('store.urls')),
]

# Serve static & media in all modes (this is a local POS app)
urlpatterns += [
    re_path(r'^static/(?P<path>.*)$', serve_static),
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]
