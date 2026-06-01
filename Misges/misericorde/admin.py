from django.contrib import admin
from .models import Service, Schedule, ContactMessage, SiteContent

admin.site.register(Service)
admin.site.register(Schedule)
admin.site.register(ContactMessage)
admin.site.register(SiteContent)
