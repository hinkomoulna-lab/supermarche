from django.shortcuts import render, redirect
from django.contrib import messages

from .models import Service, Schedule, SiteContent, ContactMessage


def home(request):
    services = Service.objects.all()
    schedules = Schedule.objects.all()
    contents = {c.key: c.value for c in SiteContent.objects.all()}
    return render(request, 'misericorde/home.html', {
        'services': services,
        'schedules': schedules,
        'contents': contents,
    })


def contact(request):
    if request.method == 'POST':
        ContactMessage.objects.create(
            name=request.POST.get('name', ''),
            email=request.POST.get('email', ''),
            phone=request.POST.get('phone', ''),
            subject=request.POST.get('subject', ''),
            message=request.POST.get('message', ''),
        )
        messages.success(request, 'Message envoyé avec succès !')
        return redirect('misericorde:home')
    return redirect('misericorde:home')
