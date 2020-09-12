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
    "browse_fields": settings.app_settings.get("browse_fields"),
}
if base_context["browse_fields"] is None:
    base_context["browse_fields"] = list(models.fieldnames)


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
        print(f"statistics: {statistics}")
        context = {
            "countjson": json.dumps(
                [
                    {
                        "n": key,
                        "c": value,
                    }
                    for key, value in statistics["counts"].items()
                ]
            ),
            "title": f"{base_context['toolname']}: statistics",
        }
        context.update(base_context)
        return render(request, "statistics.html", context)
    else:
        return login_redirect(request)


def _nicestr(item):
    if isinstance(item, list):
        joiner = ", "
        if any("," in thing for thing in item):
            joiner = "; "
        return joiner.join(thing for thing in item)
    else:
        return str(item)


def browse(request, by=None, item=None):
    if by is None:
        context = {"title": f"{base_context['toolname']}: Browse"}
        context.update(base_context)
        return render(request, "browse.html", context)
    elif item is None:
        assert by in models.browse_counts
        context = {
            "title": f"{base_context['toolname']}: Browse: {by}",
            "browse_by": by,
            "countjson": json.dumps(
                [
                    {"n": key, "c": value}
                    for key, value in models.browse_counts[by].items()
                ]
            ),
        }
        context.update(base_context)
        return render(request, "browse_by.html", context)
    else:
        assert by in models.browse_counts
        all_data = models.get_papers(by, item)
        data = []
        for item2 in all_data:
            result = {field: _nicestr(item2[field]) for field in item2["field_order"]}
            result["title"] = item2["title"]
            result["_id"] = str(item2["_id"])
            result["status"] = item2["status"]
            data.append(result)
        context = {
            "title": f"{base_context['toolname']}: Browse: {by}: {item}",
            "browse_by": by,
            "browse_by_value": item,
            "fieldnames": settings.app_settings["browse_fields"],
            "countjson": json.dumps(data),
        }
        context.update(base_context)
        return render(request, "browse_by_value.html", context)
