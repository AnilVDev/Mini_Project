from django import template
from app.models import CartItem

register = template.Library()

@register.filter(name='filter_brand')
def filter_brand(products, brand_name):
    # Implement your filter logic here
    return products.filter(brand__name=brand_name)



@register.filter(name='is_in_cart')
def is_in_cart(product, user):
    if user.is_authenticated:
        cart_item_exists = CartItem.objects.filter(cart__user=user, product_id=product.id).exists()
        return cart_item_exists

    return False