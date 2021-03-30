"""Project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.views.debug import default_urlconf
from django.contrib.auth import views
from django.urls import path, re_path
from . import pipeline_views
from .settings import pipelinebase, app_settings


def prebase(url):
    return url


urlpatterns = [
    path(prebase(""), pipeline_views.index, name="index"),
    re_path(
        "^" + prebase("statistics$(?i)"), pipeline_views.statistics, name="statistics"
    ),
    re_path("^" + prebase("login$(?i)"), pipeline_views.my_login, name="login"),
    re_path("^" + prebase("logout$(?i)"), pipeline_views.my_logout, name="logout"),
    path(prebase("browse/<slug:by>/<item>"), pipeline_views.browse, name="browse"),
    path(
        prebase("review_by_id/<slug:id>"),
        pipeline_views.review_by_id,
        name="review_by_id",
    ),
    path(prebase("review/<slug:status>"), pipeline_views.review, name="review"),
    path(
        prebase("draft_solicitation"),
        pipeline_views.draft_solicitation,
        name="draft_solicitation",
    ),
    path(prebase("browse/<slug:by>"), pipeline_views.browse, name="browse"),
    path(prebase("browse"), pipeline_views.browse, name="browse"),
    path(prebase("update/<slug:id>"), pipeline_views.update, name="update"),
    path(prebase("admin/"), admin.site.urls),
    path(prebase("change-password"), pipeline_views.change_password),
]

if "pipeline_annotation" in app_settings:
    urlpatterns.append(
        path(prebase("annotate"), pipeline_views.annotate, name="annotate")
    )

if app_settings.get("allow_db_query"):
    urlpatterns.append(path(prebase("query"), pipeline_views.query, name="query"))

if app_settings.get("allow_db_query"):
    urlpatterns.append(
        path(
            prebase("getuserdataquery"),
            pipeline_views.getuserdataquery,
            name="getuserdataquery",
        )
    )

if app_settings.get("userentry"):
    urlpatterns.append(
        path(prebase("entry/<slug:paper_id>"), pipeline_views.entry, name="entry")
    )
    urlpatterns.append(
        path(prebase("thankyou"), pipeline_views.thankyou, name="thankyou")
    )
    urlpatterns.append(
        path(
            prebase("update_userdata/<slug:id>"),
            pipeline_views.update_userdata,
            name="update_userdata",
        )
    )

if app_settings.get("data"):
    urlpatterns.append(
        path(prebase("data/<slug:paper_id>"), pipeline_views.data, name="data")
    )
