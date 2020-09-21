from django import template

register = template.Library()


@register.filter
def get_type(value):
    return str(type(value)).split("'")[1]


@register.filter
def get_label(value):
    return value.split(":")[0].strip()


@register.filter
def get_sentence(value):
    try:
        caption = value.split(":")[1]
    except:
        caption = value
    return caption.split(".")[0].strip() + "."
