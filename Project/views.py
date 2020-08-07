from django.shortcuts import redirect, render
from django.http import HttpResponse

def index(request):
    context = {"title": "Alz-Explorer"}
    return render(request, "index.html", context)