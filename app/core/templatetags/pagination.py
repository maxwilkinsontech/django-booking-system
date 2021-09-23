from django import template

register = template.Library()


@register.simple_tag
def url_replace(request, field, value):
    """
    Remove the given field from the GET parameters, keeping the others.
    """
    dict_ = request.GET.copy()
    dict_[field] = value
    return dict_.urlencode()
