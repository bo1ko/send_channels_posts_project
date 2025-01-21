from django.shortcuts import render
from .models import TelegramChannel

def index(request):
    channels = TelegramChannel.objects.all()
    
    context = {
        'channels': channels
    }

    return render(request, 'custom_admin/index.html', context)

def add_channel(request):
    return render(request, 'custom_admin/add_channel.html')