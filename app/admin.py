from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .forms import CustomerRegistrationForm
from django.contrib.auth.models import User
from django.utils.html import format_html

from .models import (
    Customer,Wallet,Transaction,
    Product,
    Cart,
    CartItem,
    ProductImage,
    Brand,
    Category,
    Order,
    OrderItem,
    BillingAddress,ShippingAddress,
    Review,ProductOffer,CategoryOffer,ReferralOffer
)


admin.site.login_template = 'app/admin_login.html'
# Register your models here.
@admin.register(Customer)
class CustomerModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'name','phone_number', 'locality', 'city', 'pincode', 'state']
@admin.register(Product)
class ProductModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'title','stock', 'selling_price', 'discount_price', 'description', 'details', 'brand', 'category', 'display_product_images']

    def display_product_images(self, obj):
        if obj.images.all():  # Check if there are associated images
            first_image = obj.images.first()
            return format_html('<img src="{}" width="50" height="50" />', first_image.image.url)
        else:
            return 'No Image'

    display_product_images.short_description = 'Product Image'

@admin.register(ProductImage)
class PoductImageModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'product', 'image']

@admin.register(Category)
class CategoryModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']

@admin.register(Brand)
class BrandModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']

@admin.register(Cart)
class CartModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'user']


@admin.register(CartItem)
class CartItemModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'cart', 'product', 'quantity']


@admin.register(Order)
class OrderModelAdmin(admin.ModelAdmin):
    list_display = ['id','user', 'billing_address', 'shipping_address', 'order_status', 'ordered_date', 'username', 'discount', 'total_price', 'payment_method']

@admin.register(OrderItem)
class OrderItemModelAdmin(admin.ModelAdmin):
    list_display = ['id','order', 'product', 'quantity', 'price_per_product']


@admin.register(BillingAddress)
class BillingAddressModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'name','phone_number', 'locality', 'city', 'pincode', 'state']

@admin.register(ShippingAddress)
class ShippingAddressModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'name','phone_number', 'locality', 'city', 'pincode', 'state']

@admin.register(Review)
class ReviewModelAdmin(admin.ModelAdmin):
    list_display = ['id','user','product','text','rating','created_at']

@admin.register(ProductOffer)
class ProductModelAdmin(admin.ModelAdmin):
    list_display = ('id','product', 'discount_percentage', 'max_discount_amount', 'start_date', 'end_date', 'conditions')

@admin.register(CategoryOffer)
class CategoryOfferAdmin(admin.ModelAdmin):
    list_display = ('id','category', 'discount_percentage', 'max_discount_amount', 'start_date', 'end_date', 'conditions')

@admin.register(ReferralOffer)
class ReferralOfferAdmin(admin.ModelAdmin):
    list_display = ('id','referrer', 'referred_user', 'created_at')

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('id','user','balance')

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id','user','amount','transaction_type','timestamp','transaction_balance')




