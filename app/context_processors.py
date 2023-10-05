from .models import Wishlist,CartItem
from app.views import calculate_cart_total
from django.urls import resolve
def user_wishlist(request):
    if request.user.is_authenticated:
        user_wishlist = Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True)
    else:
        user_wishlist = []

    return {'user_wishlist': user_wishlist}



def user_cart(request):
    if request.user.is_authenticated:
        cart_items = CartItem.objects.filter(cart__user=request.user)
        total_price = calculate_cart_total(cart_items)
    else:
        cart_items = []
        total_price = 0

    return {'cart_items': cart_items,'total_price': total_price}





def cart_context(request):
    cart_item_exists = False

    if request.user.is_authenticated:
        resolved_url = resolve(request.path_info)
        if resolved_url.url_name == 'product_detail':
            product_id = resolved_url.kwargs.get('product_id')

            cart_item_exists = CartItem.objects.filter(cart__user=request.user, product_id=product_id).exists()

    return {'cart_item_exists': cart_item_exists}

