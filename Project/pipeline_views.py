import json
from django.shortcuts import redirect, render
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from . import settings
from . import pipeline_models as models


base_context = {
    "footerhtml": settings.app_settings.get("footerhtml", ""),
    "pipelinebase": settings.app_settings.get("pipelinebase", ""),
    "toolname": settings.app_settings.get("toolname", "Pipeline"),
    "browse_fields": settings.app_settings.get("browse_fields"),
    "buttons": settings.app_settings["pipeline_review_buttons"],
    "annotation": settings.app_settings.get("pipeline_annotation"),
}

try:
    with open(
        settings.app_settings["pipeline_annotation"][
            "pipeline_metadata_autocomplete_file"
        ]
    ) as f:
        metadata_autcomplete_tags = json.load(f)
except:
    metadata_autcomplete_tags = {}


if base_context["browse_fields"] is None:
    base_context["browse_fields"] = list(models.fieldnames)


def index(request):
    context = {"title": base_context["toolname"]}
    context.update(base_context)
    return render(request, "index.html", context)


def annotate(request):
    if request.user.has_perm("auth.pipeline_annotate"):
        queue = base_context["annotation"]["queue_in"]
        context = {
            "items": [
                _prep_paper_for_review(paper)
                for paper in _filter_papers(request, models.papers_by_status(queue))
            ],
            "title": f"{base_context['toolname']}: annotate",
        }
        context.update(base_context)
        return render(request, "pipeline/annotate.html", context)
    else:
        return login_redirect(request)


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
    if request.user.has_perm("auth.pipeline_statistics"):
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
    if request.user.has_perm("auth.pipeline_browse"):
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
        "notes": paper.get("notes", ""),
        "metadata": {key: _nicestr(paper[key]) for key in paper["field_order"]},
    }


def review_by_id(request, id=None):
    if request.user.has_perm("auth.pipeline_review"):
        context = {
            "items": [_prep_paper_for_review(models.paper_by_id(id))],
            "title": f"{base_context['toolname']}: review",
        }
        context.update(base_context)
        return render(request, "pipeline/review.html", context)
    else:
        return login_redirect(request)


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
    if request.user.has_perm("auth.pipeline_review"):
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
    # TODO: as we can expand to more pipeline stages, make sure permissions match fields being updated
    if request.user.has_perm("auth.pipeline_review"):
        models.update(
            id,
            title=request.POST.get("title"),
            url=request.POST.get("url"),
            status=request.POST.get("status"),
            notes=request.POST.get("notes"),
        )
        return HttpResponse("success")
    else:
        return HttpResponse("403 Forbidden", status=403)


def change_password(request):
    if request.user.is_authenticated:
        if request.method == "POST":
            form = PasswordChangeForm(request.user, request.POST)
            if form.is_valid():
                user = form.save()
                update_session_auth_hash(request, user)
                next_url = request.POST.get("next", base_context["pipelinebase"])
                if not next_url:
                    next_url = "/"
                return redirect(next_url)
        else:
            form = PasswordChangeForm(request.user)
        context = dict(base_context)
        context["form"] = form
        context["next"] = request.GET.get("next")
        return render(request, "pipeline/change_password.html", context)
    else:
        return login_redirect(request)
