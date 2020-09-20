import json
from django.shortcuts import redirect, render
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from . import settings
from . import pipeline_models as models
from . import pipeline_permissions as permissions

base_context = {
    "footerhtml": settings.app_settings.get("footerhtml", ""),
    "pipelinebase": settings.app_settings.get("pipelinebase", ""),
    "toolname": settings.app_settings.get("toolname", "Pipeline"),
    "browse_fields": settings.app_settings.get("browse_fields"),
    "buttons": settings.app_settings["pipeline_review_buttons"],
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
        next_url = request.POST.get("next", "/")
        if user is not None:
            login(request, user)
            return redirect(next_url)
    else:
        next_url = request.GET.get("next", "/")
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
        return render(request, "pipeline/statistics.html", context)
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


def _process_paper_browse(paper):
    result = {field: _nicestr(paper[field]) for field in paper["field_order"]}
    result["title"] = paper["title"]
    result["_id"] = str(paper["_id"])
    result["status"] = paper["status"]
    return result


def browse(request, by=None, item=None):
    if permissions.statistics(request):
        if by is None:
            context = {"title": f"{base_context['toolname']}: Browse"}
            context.update(base_context)
            return render(request, "pipeline/browse.html", context)
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
            return render(request, "pipeline/browse_by.html", context)
        else:
            assert by in models.browse_counts
            all_data = models.get_papers(by, item)
            data = [_process_paper_browse(paper) for paper in all_data]
            context = {
                "title": f"{base_context['toolname']}: Browse: {by}: {item}",
                "browse_by": by,
                "browse_by_value": item,
                "fieldnames": settings.app_settings["browse_fields"],
                "countjson": json.dumps(data),
            }
            context.update(base_context)
            return render(request, "pipeline/browse_by_value.html", context)
    else:
        return login_redirect(request)


def _prep_paper_for_review(paper):
    return {
        "id": str(paper["_id"]),
        "title": paper["title"],
        "url": paper["url"],
        "metadata": {key: _nicestr(paper[key]) for key in paper["field_order"]},
    }


def review_by_id(request, id=None):
    context = {
        "items": [_prep_paper_for_review(models.paper_by_id(id))],
        "title": f"{base_context['toolname']}: review",
    }
    context.update(base_context)
    return render(request, "pipeline/review.html", context)


def _get_subset(iterable, filter_rule, start, num):
    ignore_count = 0
    keep_count = 0
    for item in iterable:
        if filter_rule(item):
            if ignore_count < start:
                ignore_count += 1
            else:
                keep_count += 1
                yield item
                if keep_count >= num:
                    break


def _filter_papers(request, papers):
    start = int(request.GET.get("start", 0))
    num = int(request.GET.get("max", 100))
    # TODO: this is where we need to make sure the thing hasn't been assigned to someone else recently
    filter_rule = lambda item: True
    return list(_get_subset(papers, filter_rule, start, num))


def review(request, status=None):
    if permissions.review(request):
        context = {
            "items": [
                _prep_paper_for_review(paper)
                for paper in _filter_papers(request, models.papers_by_status(status))
            ],
            "title": f"{base_context['toolname']}: review",
            "status": status,
        }
        context.update(base_context)
        return render(request, "pipeline/review.html", context)
    else:
        return login_redirect(request)


def update(request, id=None):
    if permissions.update(request):
        models.update(
            id,
            title=request.POST.get("title"),
            url=request.POST.get("url"),
            status=request.POST.get("status"),
        )
        return HttpResponse("success")
    else:
        return HttpResponse("403 Forbidden", status=403)
