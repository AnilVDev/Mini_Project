from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .forms import CustomerRegistrationForm
from django.contrib.auth.models import User

from .models import (
    Customer,
    Product,
    Cart,
    OrderPlaced
)
# Register your models here.
@admin.register(Customer)
class CustomerModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'name','phone_number', 'locality', 'city', 'pincode', 'state']

@admin.register(Product)
class ProductModelAdmin(admin.ModelAdmin):
    list_display = ['id','title', 'selling_price','discount_price', 'description', 'brand', 'category', 'product_image']


# class CustomUserAdmin(UserAdmin):
#     add_form = CustomerRegistrationForm
#     fieldsets = (
#         (None, {'fields': ('username', 'password1', 'password2')}),
#         ('Personal Info', {'fields': ('email', 'phonenumber')}),
#         ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
#         ('Important dates', {'fields': ('last_login', 'date_joined')}),
#     )
#
# admin.site.unregister(User)
# admin.site.register(User, CustomUserAdmin)
