from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse


class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        allowed_prefixes = (
            reverse('login'),
            '/admin/',
            settings.STATIC_URL,
            settings.MEDIA_URL,
        )

        if request.path.startswith(allowed_prefixes):
            return self.get_response(request)

        if not request.user.is_authenticated:
            return redirect(f"{reverse('login')}?next={request.path}")

        return self.get_response(request)
