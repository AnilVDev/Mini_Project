from django import template
from app.models import Wishlist

register = template.Library()

@register.simple_tag
def wishlist_count(user):
    if user.is_authenticated:
        return Wishlist.objects.filter(user=user).count()
    else:
        return 0
