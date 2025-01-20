from django.shortcuts import render

def index(request):
    return render(request, 'custom_admin/index.html')
