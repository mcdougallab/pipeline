"""
WSGI config for Project project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/howto/deployment/wsgi/
"""

import os, sys

# Calculate the path based on the location of the WSGI script.
apache_configuration = os.path.dirname(__file__)
project = os.path.dirname(apache_configuration)
workspace = os.path.dirname(project)
sys.path.append(workspace)

# sys.path.append("/opt/bitnami/apps/django/django_projects/Project")
# os.environ.setdefault(
#    "PYTHON_EGG_CACHE", "/opt/bitnami/apps/django/django_projects/Project/egg_cache"
# )


from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Project.settings")

application = get_wsgi_application()
