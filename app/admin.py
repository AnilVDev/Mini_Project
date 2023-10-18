from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .forms import CustomerRegistrationForm
from django.contrib.auth.models import User
from django.utils.html import format_html

from .models import (
    Customer,
    Product,
    Cart,
    CartItem,
    ProductImage,
    Brand,
    Category,
    Order,
    OrderItem,
    BillingAddress,ShippingAddress,
    Review,
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
    list_display = ['id','user', 'billing_address', 'shipping_address', 'order_status', 'ordered_date', 'username', 'total_price']

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

# class CustomUserAdmin(UserAdmin):
#     add_form = CustomerRegistrationForm
#     fieldsets = (
#         (None, {'fields': ('username', 'password1', 'password2')}),
#         ('Personal Info', {'fields': ('email', 'phonenumber')}),
#         ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
#         ('Important dates', {'fields': ('last_login', 'date_joined')}),
#     )


