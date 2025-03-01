# In custom_filters.py
from django import template
import markdown


register = template.Library()


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, "N/A")


@register.filter(name="mark_down")
def mark_down(text):
    return markdown.markdown(text, extensions=["fenced_code", "codehilite"])
