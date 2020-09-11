import json
from django.shortcuts import redirect, render
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from . import settings
from . import models
from . import permissions

base_context = {
    "footerhtml": settings.app_settings.get("footerhtml", ""),
    "pipelinebase": settings.app_settings.get("pipelinebase", ""),
    "toolname": settings.app_settings.get("toolname", "Pipeline"),
}


def index(request):
    context = {"title": base_context["toolname"]}
    context.update(base_context)
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
    context.update(base_context)
    return render(request, "login.html", context)


def my_logout(request):
    logout(request)
    next_url = request.GET.get("next")
    if next_url:
        return redirect(next_url)
    else:
        return redirect(base_context["pipelinebase"])


def login_redirect(request):
    return redirect(f"{base_context['pipelinebase']}/login?next={request.path}")


def statistics(request):
    if permissions.statistics(request):
        statistics = models.statistics()
        context = {
            "countjson": json.dumps(
                {
                    "n": list(statistics["counts"].keys()),
                    "c": list(statistics["counts"].values()),
                }
            ),
            "title": f"{base_context['toolname']}: statistics",
        }
        context.update(base_context)
        return render(request, "statistics.html", context)
    else:
        return login_redirect(request)
