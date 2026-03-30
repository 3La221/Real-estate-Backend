from django import template

register = template.Library()


@register.filter
def get_by_id(queryset, id):
    try:
        return queryset.get(id=id).name
    except:
        return ""


@register.filter
def get_attr(obj, attr):
    return getattr(obj, attr, "")
