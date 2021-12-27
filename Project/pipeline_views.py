import json
from django.shortcuts import redirect, render
from django.http import HttpResponse, Http404, JsonResponse
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.views.decorators.csrf import csrf_protect
from . import settings
from . import pipeline_models as models
import random
import datetime
from datetime import datetime

base_context = {
    "footerhtml": settings.app_settings.get("footerhtml", ""),
    "pipelinebase": settings.app_settings.get("pipelinebase", ""),
    "toolname": settings.app_settings.get("toolname", "Pipeline"),
    "browse_fields": settings.app_settings.get("browse_fields"),
    "submit_button_text": settings.app_settings["submit_button_text"],
    "buttons": settings.app_settings["pipeline_review_buttons"],
    "annotation": settings.app_settings.get("pipeline_annotation"),
    "has_draft_solicitations": "draft_solicitations" in settings.app_settings,
    "allow_db_query": settings.app_settings.get("allow_db_query", False),
    "public_submission_list": settings.app_settings.get("public_submission_list", False),
    "highlight_fields": settings.app_settings.get("highlight_fields", []),
    "highlight_words": settings.app_settings.get("highlight_words", []),
    "sitestyles": settings.app_settings.get("css", ""),
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

index_content_filename = settings.app_settings.get("index-content")
index_content = ""
if index_content_filename:
    # try:
    with open(index_content_filename) as f:
        index_content = f.read()
    # except:
    pass


def index(request):
    context = {"title": base_context["toolname"], "index_content": index_content}
    context.update(base_context)
    return render(request, "index.html", context)


@csrf_protect
def annotate(request):
    if request.user.has_perm("auth.pipeline_annotate"):
        queue = base_context["annotation"]["queue_in"]
        context = {
            "items": [
                _prep_paper_for_annotate(paper)
                for paper in _filter_papers(request, models.papers_by_status(queue))
            ],
            "title": f"{base_context['toolname']}: annotate",
        }
        context.update(base_context)
        return render(request, "pipeline/annotate.html", context)
    else:
        return login_redirect(request)


@csrf_protect
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
        response = redirect(next_url)
    else:
        response = redirect(base_context["pipelinebase"])
    response.delete_cookie("csrftoken")
    return response


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
    result = {field: _nicestr(paper[field]) for field in paper.get("field_order", [])}
    result["title"] = paper.get("title", "")
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
        "title": paper.get("title", ""),
        "url": paper.get("url"),
        "notes": paper.get("notes", ""),
        "metadata": {key: _nicestr(paper[key]) for key in paper.get("field_order", [])},
    }


def _prep_paper_for_annotate(paper):
    result = _prep_paper_for_review(paper)
    annotations = paper.get("annotation", {}).get("field", {})
    result["field"] = [
        {
            "name": item["name"],
            "value": annotations.get(item["short_name"], ""),
            "type": item["type"],
            "short_name": item["short_name"],
            "placeholder": item.get("placeholder"),
        }
        for item in base_context["annotation"]["fields"]
    ]
    return result


@csrf_protect
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
    if settings.app_settings.get("random_paper_order"):
        items = list(papers)
        random.shuffle(items)
        # TODO: remove this hard-coded size
        return items[:10]
    # TODO: this is where we need to make sure the thing hasn't been assigned to someone else recently
    filter_rule = lambda item: True
    return list(_get_subset(papers, filter_rule, start, num))


@csrf_protect
def review(request, status=None):
    if request.user.has_perm("auth.pipeline_review"):
        guidelines = (
            settings.app_settings.get("triage_guidelines", "")
            if status == "triage"
            else ""
        )
        context = {
            "items": [
                _prep_paper_for_review(paper)
                for paper in _filter_papers(request, models.papers_by_status(status))
            ],
            "title": f"{base_context['toolname']}: review",
            "status": status,
            "guidelines": guidelines,
        }
        context.update(base_context)
        return render(request, "pipeline/review.html", context)
    else:
        return login_redirect(request)


@csrf_protect
def draft_solicitation(request):
    if request.user.has_perm("auth.pipeline_draft_solicitation"):
        try:
            my_settings = settings.app_settings["draft_solicitations"]
        except:
            raise Http404("No such URL")
        context = {
            "items": [
                _prep_paper_for_review(paper)
                for paper in _filter_papers(
                    request, models.papers_by_status(my_settings["queue"])
                )
            ],
            "title": f"{base_context['toolname']}: draft solicitations",
            "status": f"{base_context['toolname']}: draft solicitations",
            "templates_json": json.dumps(my_settings["templates"]),
            "templates": my_settings["templates"],
        }
        context.update(base_context)
        context["buttons"] = my_settings["buttons"]
        return render(request, "pipeline/solicit.html", context)
    else:
        return login_redirect(request)


@csrf_protect
def sublist(request, paper_id=None):
    context = dict(base_context)
    context["userentry"] = settings.app_settings.get("userentry", {})
    if request.user.has_perm("auth.pipeline_browse") or context["public_submission_list"]:
        if paper_id is None:
            docs = models.getdocsforuserdata()
            results = {}
            updatedates = {}
            for item in docs:
                results[str(item["_id"])] = item.get("title", "")
                initdate = item.get("init_date", "")
                changedate = item.get("change_date", "")
                if changedate:
                    idate = changedate
                else:
                    idate = initdate
                if len(str(idate)) > 0:
                    d1 = datetime.strptime(str(idate), "%Y-%m-%d %H:%M:%S.%f")
                    new_format = "%Y-%m-%d"
                    updatedates[str(item["_id"])] = d1.strftime(new_format)
                else:
                    updatedates[str(item["_id"])] = idate
            default = ""
            context = {
                "docs": json.dumps(
                    [
                        {
                            "id": key,
                            "title": value,
                            "dateOf": str(updatedates.get(key, default)),
                        }
                        for key, value in results.items()
                    ]
                ),
            }
            context.update(base_context)
            return render(request, "pipeline/sublist.html", context)
        else:
            try:
                context["userdata"] = json.dumps(models.get_userdata(paper_id, False))
            except:
                raise Http404("Not found")
            context["paper_id"] = paper_id
            data = settings.app_settings.get("data", {})
            context["header"] = data.get("header", "")
            context["title"] = f"{base_context['toolname']}: {data.get('title')}"
            context["pagetitle"] = data.get("title", "")
            context["readonly"] = True
            return render(request, "pipeline/entry.html", context)
    else:
        return login_redirect(request)


# datetimes are not JSON serializable
def textify_datetime(obj):
    if isinstance(obj, list):
        loop_over = range(len(obj))
    else:
        loop_over = obj.keys()
    for key in loop_over:
        item = obj[key]
        if isinstance(item, list) or isinstance(item, dict):
            obj[key] = textify_datetime(item)
        elif isinstance(item, datetime):
            obj[key] = str(item)
    return obj


@csrf_protect
def query(request):
    """process user submitted db queries"""
    if request.user.has_perm("auth.pipeline_db_query"):
        lookfor = request.POST.get("q")
        context = dict(base_context)
        if lookfor:
            lookfor = json.loads(lookfor)
            results = []
            for item in models.query(lookfor):
                item["_id"] = str(item["_id"])
                results.append(textify_datetime(item))
            context["result"] = json.dumps(results, indent=2)
            return render(request, "pipeline/query_results.html", context)
        else:
            return render(request, "pipeline/query.html", context)
    else:
        return login_redirect(request)


@csrf_protect
def getuserdataquery(request):
    if request.user.has_perm("auth.pipeline_db_query"):
        response = JsonResponse(models.getdocsforuserdata(), safe=False)
        response["Content-Disposition"] = f"attachment; filename=userdata.json"
        return response
    else:
        return login_redirect(request)


def thankyou(request):
    context = dict(base_context)
    context["title"] = f"{base_context['toolname']}: Thank you"

    return render(request, "pipeline/thankyou.html", context)


# NOTE: to allow cookieless users, this does not use csrfprotect
def update_userdata(request, id=None):
    try:
        userdata = json.loads(request.POST.get("userdata", "{}"))
        if not userdata:
            return HttpResponse("400 Bad Request", status=400)
        models.update_userdata(id, userdata)
        return HttpResponse("success")
    except:
        return HttpResponse("403 Forbidden", status=403)


@csrf_protect
def update(request, id=None):
    # TODO: as we can expand to more pipeline stages, make sure permissions match fields being updated
    if (
        request.user.has_perm("auth.pipeline_review")
        or request.user.has_perm("auth.pipeline_annotate")
        or request.user.has_perm("auth.pipeline_draft_solicitation")
    ):
        changes = {}
        for key, value in request.POST.items():
            if key in ["title", "url", "status", "notes"]:
                # these can be changed by anybody who can do updates
                pass
            elif (
                key == "annotation.metadata_tags" or key.startswith("annotation.field.")
            ) and request.user.has_perm("auth.pipeline_annotate"):
                if key == "annotation.metadata_tags":
                    value = json.loads(value)
            elif request.user.has_perm("auth.pipeline_draft_solicitation") and key in (
                "email",
                "email_address",
                "email_subject",
            ):
                pass
            else:
                return HttpResponse("403 Forbidden", status=403)
            changes[key] = value
        models.update(id, request.user.username, **changes)
        return HttpResponse("success")
    else:
        return HttpResponse("403 Forbidden", status=403)


@csrf_protect
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


def entry(request, paper_id=None):
    context = dict(base_context)
    context["userentry"] = settings.app_settings.get("userentry", {})
    context["solicit_message_template"] = settings.app_settings.get(
        "solicit_message_template"
    )
    context["solicit_subject_template"] = settings.app_settings.get(
        "solicit_subject_template"
    )
    context["solicit_email_field"] = settings.app_settings.get("solicit_email_field")
    if paper_id == "new":
        context["userdata"] = "{}"
    else:
        try:
            context["userdata"] = json.dumps(models.get_userdata(paper_id, False))
        except:
            context["userdata"] = "{}"
    context["paper_id"] = paper_id
    context[
        "title"
    ] = f"{base_context['toolname']}: {context['userentry'].get('title')}"
    context["header"] = context["userentry"].get("header", "")
    context["readonly"] = False
    context["pagetitle"] = context["userentry"].get("title", "")
    return render(request, "pipeline/entry.html", context)


def data(request, paper_id=None):
    private_user = False
    context = dict(base_context)
    context["userentry"] = settings.app_settings.get("userentry", {})
    if request.user.is_authenticated:
        private_user = True
    try:
        context["userdata"] = json.dumps(models.get_userdata(paper_id, private_user))
    except:
        raise Http404("Not found")
    context["paper_id"] = paper_id
    data = settings.app_settings.get("data", {})
    context["header"] = data.get("header", "")
    context["title"] = f"{base_context['toolname']}: {data.get('title')}"
    context["pagetitle"] = data.get("title", "")
    context["readonly"] = True
    return render(request, "pipeline/entry.html", context)
