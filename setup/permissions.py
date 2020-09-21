from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

user_type = ContentType.objects.get(app_label="auth", model="user")

Permission.objects.get_or_create(
    codename="pipeline_statistics",
    name="Can see pipeline statistics",
    content_type=user_type,
)

Permission.objects.get_or_create(
    codename="pipeline_review", name="Can do pipeline reviews", content_type=user_type
)

Permission.objects.get_or_create(
    codename="pipeline_browse", name="Can browse pipeline", content_type=user_type
)

Permission.objects.get_or_create(
    codename="pipeline_annotate",
    name="Can annotate in pipeline",
    content_type=user_type,
)

Permission.objects.get_or_create(
    codename="pipeline_draft_solicitation",
    name="Can draft solicitations in pipeline",
    content_type=user_type,
)

Permission.objects.get_or_create(
    codename="pipeline_send_solicitation",
    name="Can send solicitations in pipeline",
    content_type=user_type,
)