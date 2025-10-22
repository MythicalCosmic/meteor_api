from django import template

register = template.Library()

# Restore 'length_is' filter (removed from Django 5+)
@register.filter
def length_is(value, arg):
    try:
        return len(value) == int(arg)
    except Exception:
        return False
