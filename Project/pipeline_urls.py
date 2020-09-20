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
from django.urls import path, re_path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    re_path("^statistics$(?i)", views.statistics, name="statistics"),
    re_path("^login$(?i)", views.my_login, name="login"),
    re_path("^logout$(?i)", views.my_logout, name="logout"),
    path("browse/<slug:by>/<item>", views.browse, name="browse"),
    path("review_by_id/<slug:id>", views.review_by_id, name="review_by_id"),
    path("review/<slug:status>", views.review, name="review"),
    path("browse/<slug:by>", views.browse, name="browse"),
    path("browse", views.browse, name="browse"),
    path("update/<slug:id>", views.update, name="update"),
]
