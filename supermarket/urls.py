from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.views.static import serve
from store.forms import LoginForm

urlpatterns = [
    path('admin/', admin.site.urls),
    path('connexion/', auth_views.LoginView.as_view(
        template_name='registration/login.html',
        authentication_form=LoginForm,
    ), name='login'),
    path('deconnexion/', auth_views.LogoutView.as_view(), name='logout'),
    path('', include('store.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    ]
