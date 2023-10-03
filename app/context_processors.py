from .models import Wishlist


def user_wishlist(request):
    if request.user.is_authenticated:
        user_wishlist = Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True)
    else:
        user_wishlist = []

    return {'user_wishlist': user_wishlist}