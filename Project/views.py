from django.shortcuts import redirect, render
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout


def index(request):
    context = {"title": "Alz-Explorer"}
    return render(request, "index.html", context)


def my_login(request):
    username = request.POST.get("username")
    password = request.POST.get("password")
    if password is not None:
        user = authenticate(username=username, password=password)
        next_url = request.POST.get("next")
        if user is not None:
            login(request, user)
            return redirect(request.POST.get("next"))
    else:
        next_url = request.GET.get("next")
    context = {"next": next_url}
    return render(request, "login.html", context)


def my_logout(request):
    logout(request)
    next_url = request.GET.get("next")
    if next_url:
        return redirect(next_url)
    else:
        return redirect("/")
