from django import template

register = template.Library()

@register.simple_tag
def page_range(current, total, window=2):
    start = max(current - window, 1)
    end = min(current + window + 1, total + 1)
    return range(start, end)