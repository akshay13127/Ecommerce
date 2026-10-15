# yourapp/templatetags/range_filter.py

from django import template

register = template.Library()

@register.filter
def range(value):
    try:
        value = int(value)
        return range(1, value + 1)
    except:
        return []
