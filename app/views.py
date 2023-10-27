import random
from django.shortcuts import render,redirect,get_object_or_404
from django.views import View
from .models import Customer,Cart,Product,OrderPlaced,ProductImage,Category,Brand,Wishlist,CartItem,Order,OrderItem,BillingAddress,ShippingAddress,Review,ProductOffer,ReferralOffer,CategoryOffer

from .forms import CustomerRegistrationForm,CustomerProfileForm,ProductForm, CustomAdminLoginForm, MyPasswordChangeForm, OTPVerificationForm, ProductImageFormSet, ProductImageForm,CategoryForm,BrandForm,UserProfileForm,ProductOfferForm,ReferralOfferForm,CategoryOfferForm,MonthYearForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.forms import modelformset_factory
from django.db.models import Q,Count
from django.contrib.auth import views as auth_views
from django.urls import reverse
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.views import LoginView
from django.contrib.auth.forms import AuthenticationForm
from django.views.decorators.cache import never_cache
from django.contrib.auth import logout
from twilio.rest import Client
import datetime
from django.conf import settings
from django.contrib.auth.models import User
from django.views.generic import ListView
from django.contrib.auth.hashers import make_password
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.template.loader import get_template
from django.http import HttpResponse
from xhtml2pdf import pisa
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.functions import ExtractMonth,ExtractDay,ExtractYear
import calendar
from decimal import Decimal,InvalidOperation



class ProductView(View):
    def get(self, request):
        products_c = Product.objects.filter(Q(category__name__icontains='camera'))
        products_sw = Product.objects.filter(Q(category__name__icontains='smart watch'))
        products_h = Product.objects.filter(Q(category__name__icontains='headphone'))
        products_sp = Product.objects.filter(Q(category__name__icontains='speaker'))
        categories = Product.objects.values_list('category__name', flat=True).distinct()
        products = list(Product.objects.all())
        random.shuffle(products)

        def sample_products(products, num_samples):
            if len(products) >= num_samples:
                return random.sample(list(products), num_samples)
            else:
                return list(products)

        camera = sample_products(list(products_c), 5)
        smartwatch = sample_products(list(products_sw), 5)
        headphone = sample_products(list(products_h), 5)
        speaker = sample_products(list(products_sp), 5)
        context = {
            'camera': camera,
            'smartwatch': smartwatch,
            'headphone':headphone,
            'speaker':speaker,
            'categories': categories,
            'products':products,

        }
        return render(request, 'app/index.html', context)


class ProductDetailView(View):
    def get(self, request,pk):
        product = get_object_or_404(Product, pk=pk)
        has_purchased_product = OrderItem.objects.filter(order__user=request.user, product=product).exists()
        print(has_purchased_product)
        product_reviews = Review.objects.filter(product=product)
        total_review_count = product_reviews.count()
        context = {
            'product': product,
            'has_purchased_product': has_purchased_product,
            'product_reviews': product_reviews,
            'total_review_count': total_review_count,
        }
        return render(request, 'app/productdetails.html', context)

def add_to_cart(request):
 return render(request, 'app/addtocart.html')

def buy_now(request,product_id):
    product = get_object_or_404(Product, pk=product_id)

    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        quantity = request.POST.get('quantity', 1)

        try:
            quantity = int(quantity)
        except ValueError:
            quantity = 1

        if quantity > product.stock:
            return redirect('product-detail', pk=product_id)

        # Check if the product is already in the cart
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        if not created:
            cart_item_exists = True
        else:
            cart_item_exists = False
            cart_item.quantity = quantity  # Set the initial quantity
            cart_item.save()
        return redirect('checkout')

@login_required
def address(request):
 add = Customer.objects.filter(user=request.user)
 return render(request, 'app/address.html', {'add':add,'active':'bg-danger'})


@login_required
def edit_address(request, address_id):
    address = get_object_or_404(Customer, pk=address_id)

    if request.method == 'POST':
        form = CustomerProfileForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            return redirect('address')
    else:
        form = CustomerProfileForm(instance=address)

    return render(request, 'app/edit_address.html', {'form': form, 'address': address})


@login_required
def delete_address(request, address_id):
    try:
        address = Customer.objects.get(pk=address_id)
        address.delete()
        messages.success(request, 'Address deleted successfully.')
    except Brand.DoesNotExist:
        messages.error(request, 'Address not found.')

    return redirect('address')


def mobile(request):
 return render(request, 'app/mobile.html')

def login(request):
 return render(request, 'app/login.html')







class CustomerRegistrationView(View):
    def get(self, request):
        form = CustomerRegistrationForm()
        return render(request, 'app/customerregistration.html', {'form': form})

    def post(self, request):
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            request.session['temp_user_data'] = {
                'username': form.cleaned_data['username'],
                'email': form.cleaned_data['email'],
                'password': form.cleaned_data['password1'],  # Replace with your password hashing logic
            }

            otp = form.generate_otp()

            # Send the OTP via Twilio
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            message = client.messages.create(
                body=f'Your OTP for registration: {otp}',
                from_=settings.TWILIO_PHONE_NUMBER,
                to = "+917012115234"
                # to=form.cleaned_data['phone_number']
            )

            # Store the OTP in the session for later verification
            request.session['registration_otp'] = otp

            messages.success(request, 'OTP sent successfully. Please verify your phone number.')

            # Redirect to the OTP verification page
            return redirect('verify_otp')

        return render(request, 'app/customerregistration.html', {'form': form})

class OTPVerificationView(View):
    MAX_ATTEMPTS = 3
    OTP_EXPIRY_MINUTES = 1

    def get(self, request):
        if 'registration_otp' in request.session:
            return render(request, 'app/verify_otp.html', {'form': OTPVerificationForm()})
        else:
            return redirect('customer_registration')

    def post(self, request):
        form = OTPVerificationForm()
        if 'registration_otp' in request.session:
            form = OTPVerificationForm(request.POST)
            if form.is_valid():
                entered_otp = form.cleaned_data['otp']
                stored_otp = request.session['registration_otp']
                if 'otp_attempts' not in request.session:
                    request.session['otp_attempts'] = 0
                otp_attempts = request.session['otp_attempts']
                now = datetime.datetime.now()

                # Check if the OTP has expired
                otp_timestamp = request.session.get('otp_timestamp')
                if otp_timestamp and (now - otp_timestamp).total_seconds() > (self.OTP_EXPIRY_MINUTES * 60):
                    del request.session['registration_otp']
                    messages.error(request, 'OTP has expired. Please request a new OTP.')
                    return redirect('customer_registration')

                if entered_otp == stored_otp:
                    user_data = request.session.get('temp_user_data')
                    user = User.objects.create(
                        username=user_data['username'],
                        email=user_data['email'],
                        password=make_password(user_data['password'])
                    )
                    del request.session['temp_user_data']
                    del request.session['registration_otp']
                    del request.session['otp_attempts']
                    messages.success(request, 'OTP verified successfully. Registration complete!')

                    return redirect('login')
                else:
                    otp_attempts += 1
                    request.session['otp_attempts'] = otp_attempts
                    if otp_attempts >= self.MAX_ATTEMPTS:
                        del request.session['registration_otp']
                        del request.session['otp_attempts']
                        messages.error(request, 'You have exceeded the maximum OTP verification attempts.')
                        return redirect('customer_registration')
                    messages.error(request, 'Invalid OTP. Please try again.')

        return render(request, 'app/verify_otp.html', {'form': form})

    def resend_otp(self, request):
        if 'registration_otp' in request.session:
            now = datetime.datetime.now()
            otp_timestamp = request.session.get('otp_timestamp')
            if not otp_timestamp or (now - otp_timestamp).total_seconds() > (self.OTP_EXPIRY_MINUTES * 60):
                # Generate a new OTP
                new_otp = generate_random_otp()
                # Send the new OTP via Twilio or any other method
                # Update the OTP timestamp
                request.session['otp_timestamp'] = now
                request.session['registration_otp'] = new_otp
                messages.success(request, 'New OTP sent successfully. Please check your phone.')
            else:
                messages.error(request, 'You can only request a new OTP after the previous one has expired.')

        return redirect('verify_otp')



def registration_complete(request):
    return render(request, 'registration_complete.html')

def max_attempts_exceeded(request):
    return render(request, 'max_attempts_exceeded.html')


@method_decorator(login_required, name='dispatch')
class ProfileView(View):
    def get(self, request):
        form = CustomerProfileForm()
        user = request.user
        referral_code = generate_referral_code(user)
        context = {
            'user': user,
            'form': form,
            'referral_code':referral_code,

        }
        return render(request, 'app/profile.html', context)

    def post(self, request):
        form = CustomerProfileForm(request.POST)
        if form.is_valid():
            usr = request.user
            name = form.cleaned_data['name']
            phone_number = form.cleaned_data['phone_number']
            locality = form.cleaned_data['locality']
            city = form.cleaned_data['city']
            state = form.cleaned_data['state']
            pincode = form.cleaned_data['pincode']
            reg = Customer(user=usr, name=name, phone_number=phone_number, locality=locality, city=city, state=state, pincode=pincode)
            reg.save()
            messages.success(request, 'Congratulations!! Address Updated Successfully')

        form = CustomerProfileForm()
        user = request.user
        context = {
            'user': user,
            'form': form,
        }
        return render(request, 'app/profile.html',context)

def edit_user_profile(request):
    if request.method == 'POST':
        user_form = UserProfileForm(request.POST, instance=request.user)

        if user_form.is_valid():
            user_form.save()
            messages.success(request, 'Your profile has been updated successfully.')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the error(s) in the form.')
            form_errors = user_form.errors
            return render(request, 'app/edit_user_profile.html', {'user_form': user_form, 'form_errors': form_errors})


    else:
        user_form = UserProfileForm(instance=request.user)

    return render(request, 'app/edit_user_profile.html', {'user_form': user_form})


@method_decorator(staff_member_required, name='dispatch')
def add_product_with_images(request):
    if request.method == 'POST':
        product_form = ProductForm(request.POST)
        image_formset = ProductImageFormSet(request.POST, request.FILES, prefix='images')

        if product_form.is_valid() and image_formset.is_valid():
            product = product_form.save()

            for image_form in image_formset:
                if image_form.cleaned_data:
                    image = image_form.save(commit=False)
                    image.product = product
                    image.save()

            return redirect('product_list')
    else:
        product_form = ProductForm()
        image_formset = ProductImageFormSet(prefix='images')

    return render(request, 'add_product_with_images.html', {'product_form': product_form, 'image_formset': image_formset})



def password_change_view(request):
    context = {
        'form_class': MyPasswordChangeForm,
        'success_url': reverse('password_change_done'),
        'active': 'bg-danger',
    }
    return auth_views.PasswordChangeView.as_view(
        template_name='app/passwordchange.html',
        extra_context=context  # Pass the context here
    )(request)


@method_decorator(staff_member_required, name='dispatch')
class CustomAdminLoginView(LoginView):
    template_name = 'admin_login.html'  # Create this template
    authentication_form = CustomAdminLoginForm

@never_cache
def admin_login(request):
    errors = None
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.is_superuser:
                login(request)
                return redirect('admin_home')
            else:
                errors = 'You are not an admin. Please use User login.'


    else:
        form = AuthenticationForm(request)

    return render(request, 'app/admin_login.html', {'form': form, 'errors': errors})



@staff_member_required
def admin_home(request):

    return render(request,'app/admin-dashboard.html')

@staff_member_required
def user_list(request):
    query = request.GET.get('q', '')
    if query:
        users = User.objects.filter( Q(username__icontains=query) | Q(email__icontains=query),is_staff=False)
    else:
        users = User.objects.filter(is_staff=False)

    paginator = Paginator(users,5)
    page_number = request.GET.get('page')
    usersfinal = paginator.get_page(page_number)
    totalpage =usersfinal.paginator.num_pages
    page_range = range(usersfinal.number, min(usersfinal.number + 3,totalpage+1))

    context = {
        'users': usersfinal,
        'search_query': query,
        'lastpage': totalpage,
        'page_range':page_range
    }

    return render(request, 'app/user_list.html', context)


@staff_member_required
def is_admin_list(request):
    query = request.GET.get('q', '')
    if query:
        users = User.objects.filter( Q(username__icontains=query) | Q(email__icontains=query),is_staff=True)
        print(users)
    else:
        users = User.objects.filter(is_staff=True)

    paginator = Paginator(users,5)
    page_number = request.GET.get('page')
    usersfinal = paginator.get_page(page_number)
    totalpage =usersfinal.paginator.num_pages
    page_range = range(usersfinal.number, min(usersfinal.number + 3,totalpage+1))

    context = {
        'users': usersfinal,
        'search_query': query,
        'lastpage': totalpage,
        'page_range':page_range
    }

    return render(request, 'app/is_admin_list.html', context)


@method_decorator(staff_member_required, name='dispatch')
class ProductListView(ListView):
    model = Product
    template_name = 'app/product_list.html'
    context_object_name = 'products'
    paginate_by = 5

    def get(self, request, *args, **kwargs):
        query = self.request.GET.get('q', '')

        if query:
            products = Product.objects.filter(title__icontains=query)
        else:
            products = Product.objects.all()

        paginator = Paginator(products, self.paginate_by)
        page_number = self.request.GET.get('page')
        productsfinal = paginator.get_page(page_number)
        totalpage = productsfinal.paginator.num_pages
        page_range = range(productsfinal.number, min(productsfinal.number + 3, totalpage + 1))

        context = {
            'products': productsfinal,
            'search_query': query,
            'lastpage': totalpage,
            'page_range': page_range
        }

        return render(request, self.template_name, context)


@staff_member_required
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('product_list')  # Redirect to the product list page after successful submission
    else:
        form = ProductForm()

    return render(request, 'app/add_product.html', {'form': form})


@staff_member_required
def add_product_images(request, product_id):
    product = Product.objects.get(pk=product_id)
    images = ProductImage.objects.filter(product=product)

    if request.method == 'POST':
        formset = ProductImageFormSet(request.POST, request.FILES, queryset=ProductImage.objects.none())
        if formset.is_valid():
            for form in formset:
                if form.cleaned_data:
                    image = form.save(commit=False)
                    image.product = product
                    image.save()
            return redirect('add_product_image', product_id=product_id)
    else:
        formset = ProductImageFormSet(queryset=ProductImage.objects.none())

    return render(request, 'app/add_image_to_product.html', {'formset': formset, 'product': product, 'images':images})

@staff_member_required
def edit_product(request, product_id):
    product = get_object_or_404(Product, pk=product_id)

    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            return redirect('product_list')
    else:
        form = ProductForm(instance=product)

    return render(request, 'app/edit_product.html', {'form': form, 'product': product})


@staff_member_required
def delete_product(request, product_id):
    try:
        product = Product.objects.get(pk=product_id)
        product.delete()
        messages.success(request, 'Product deleted successfully.')
    except Product.DoesNotExist:
        messages.error(request, 'Product not found.')

    return redirect('product_list')

@staff_member_required
def delete_product_image(request, image_id):
    image = get_object_or_404(ProductImage, id=image_id)
    product_id = image.product.id
    image.delete()
    return redirect('add_product_image', product_id=product_id)




@staff_member_required
def category_list_and_add(request):
    query = request.GET.get('q', '')
    if query:
        categories = Category.objects.filter(name__icontains=query)
    else:
        categories = Category.objects.all()

    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category_name = form.cleaned_data['name']
            existing_category = Category.objects.filter(name__iexact=category_name).first()
            if existing_category:
                messages.error(request, 'Category with this name already exists.')
            else:
                form.save()
                messages.success(request, 'Category added successfully.')

            return redirect('category_list_and_add')
    else:
        form = CategoryForm()

    paginator = Paginator(categories, 5)
    page_number = request.GET.get('page')
    categoriesfinal = paginator.get_page(page_number)
    totalpage = categoriesfinal.paginator.num_pages
    page_range = range(categoriesfinal.number, min(categoriesfinal.number + 3, totalpage + 1))

    context = {
        'form': form,
        'categories': categoriesfinal,
        'search_query': query,
        'lastpage': totalpage,
        'page_range': page_range
    }

    return render(request, 'app/category_list_and_add.html', context)


@staff_member_required
def delete_category(request, category_id):
    try:
        category = Category.objects.get(pk=category_id)
        category.delete()
        messages.success(request, 'Category deleted successfully.')
    except Category.DoesNotExist:
        messages.error(request, 'Category not found.')

    return redirect('category_list_and_add')

@staff_member_required
def edit_category(request, category_id):
    category = get_object_or_404(Category, pk=category_id)

    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            return redirect('category_list_and_add')
    else:
        form = CategoryForm(instance=category)


    return render(request, 'app/edit_category.html', {'form': form, 'category': category})

@staff_member_required
def brand_list_and_add(request):
    query = request.GET.get('q', '')
    if query:
        brands = Brand.objects.filter(name__icontains=query)
    else:
        brands = Brand.objects.all()

    if request.method == 'POST':
        form = BrandForm(request.POST)
        if form.is_valid():
            brand_name = form.cleaned_data['name']
            existing_brand = Brand.objects.filter(name__iexact=brand_name).first()
            if existing_brand:
                messages.error(request, 'Brand with this name already exists.')
            else:
                form.save()
                messages.success(request, 'Brand added successfully.')
            return redirect('brand_list_and_add')
    else:
        form = BrandForm()

    paginator = Paginator(brands, 5)
    page_number = request.GET.get('page')
    brandsfinal = paginator.get_page(page_number)
    totalpage = brandsfinal.paginator.num_pages
    page_range = range(brandsfinal.number, min(brandsfinal.number + 3, totalpage + 1))

    context = {
        'form': form,
        'brands': brandsfinal,
        'search_query': query,
        'lastpage': totalpage,
        'page_range': page_range
    }

    return render(request, 'app/brand_list_and_add.html', context)

@staff_member_required
def delete_brand(request, brand_id):
    try:
        brand = Brand.objects.get(pk=brand_id)
        brand.delete()
        messages.success(request, 'Brand deleted successfully.')
    except Brand.DoesNotExist:
        messages.error(request, 'Brand not found.')

    return redirect('brand_list_and_add')

@staff_member_required
def edit_brand(request, brand_id):
    brand = get_object_or_404(Brand, pk=brand_id)

    if request.method == 'POST':
        form = BrandForm(request.POST, instance=brand)
        if form.is_valid():
            form.save()
            return redirect('brand_list_and_add')
    else:
        form = BrandForm(instance=brand)

    return render(request, 'app/edit_brand.html', {'form': form, 'brand': brand})

@staff_member_required
def toggle_user_status(request, user_id):
    user = get_object_or_404(User, id=user_id)

    user.is_active = not user.is_active
    user.save()

    if user.is_active:
        messages.success(request, f"User '{user.username}' is unblocked.")
    else:
        messages.warning(request, f"User '{user.username}' is blocked.")

    return redirect('user_list')


@staff_member_required
def toggle_user_credential(request, user_id):
    user = get_object_or_404(User, id=user_id)
    print('hello')
    if user.is_staff:
        user.is_staff = False
        user.is_superuser = False
        messages.success(request, f"User '{user.username}' is now a regular user.")
    else:
        user.is_staff = True
        user.is_superuser = True
        messages.warning(request, f"User '{user.username}' is now an admin.")

    user.save()
    return redirect('user_list')

@staff_member_required
def user_search(request):
    query = request.GET.get('q', '')
    users = User.objects.filter(username__icontains=query)
    return render(request, 'app/user_search.html', {'users': users})


def product_listing(request, categorys):
    print('from-',categorys)
    print('hai')
    selected_categories = request.GET.getlist('category')
    print(selected_categories)
    selected_brands = request.GET.getlist('brand')
    print(selected_brands)

    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    categories = Category.objects.all()
    brands = Brand.objects.all()

    if categorys and not selected_categories:
        products = Product.objects.filter(category__name=categorys)
        print('from categorys',products)
    else:

        if selected_categories:
            products = Product.objects.filter(category__name__in=selected_categories)
            print('selected categories',products)

        if selected_brands and not selected_categories:
            products = Product.objects.filter(brand__name__in=selected_brands)
        else:
            products = products.filter(brand__name__in=selected_brands)
            print('pro from brands-',products)


    if min_price:
        products = products.filter(discount_price__gte=min_price)

    if max_price:
        products = products.filter(discount_price__lte=max_price)

    # sort_by_price = request.GET.get('sort_by_price', '0')

    # if sort_by_price == '0':
    #     products = products.order_by('discount_price')
    # elif sort_by_price == '1':
    #     products = products.order_by('-discount_price')

    products_per_page = 6

    paginator = Paginator(products, products_per_page)
    page_number = request.GET.get('page')
    products_page = paginator.get_page(page_number)
    total_pages = paginator.num_pages
    page_range = range(1, total_pages + 1)

    context = {
        'categorys': categorys,
        'selected_categories': selected_categories,
        'selected_brands': selected_brands,
        'min_price': min_price,
        'max_price': max_price,
        'categories': categories,
        'brands': brands,
        'page_range': page_range,
        'products': products_page,

    }

    return render(request, 'app/product_listing.html', context)

def search_product(request):
    selected_category = (request.GET.get('categories', 'All Categories'))
    search_query = request.GET.get('search_query','')


    if selected_category == 'All Categories':
        products = Product.objects.all()
    else:
        products = Product.objects.filter(category__name = selected_category)

    products = products.filter(Q(title__icontains=search_query) | Q(description__icontains=search_query))

    categories = Category.objects.all()
    brands = Brand.objects.all()
    products_per_page = 6

    paginator = Paginator(products, products_per_page)
    page_number = request.GET.get('page')
    products_page = paginator.get_page(page_number)
    total_pages = paginator.num_pages
    page_range = range(1, total_pages + 1)

    context = {
        'selected_category': selected_category,
        'search_query': search_query,
        'categories': categories,
        'brands': brands,
        'page_range': page_range,
        'products': products_page,

    }

    return render(request, 'app/product_listing.html', context)


@login_required
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    user = request.user
    if not Wishlist.objects.filter(user=user, product=product).exists():
        Wishlist.objects.create(user=request.user, product=product)
    next_url = request.POST.get('next')
    if next_url:
        return redirect(next_url)
    else:
        return redirect(reverse('home'))
def remove_from_wishlist(request, product_id):
    product = Product.objects.get(pk=product_id)
    Wishlist.objects.filter(user=request.user, product=product).delete()
    return redirect('wishlist')


@login_required
def toggle_wishlist(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    user = request.user

    in_wishlist = Wishlist.objects.filter(user=user, product=product).exists()

    if in_wishlist:
        Wishlist.objects.filter(user=user, product=product).delete()
    else:
        Wishlist.objects.create(user=user, product=product)

    next_url = request.POST.get('next')
    if next_url:
        return redirect(next_url)
    else:
        return redirect(reverse('home'))



def wishlist(request):
    wishlist_items = Wishlist.objects.filter(user=request.user)
    return render(request, 'app/wishlist.html', {'wishlist_items': wishlist_items})


def cart(request):
    if request.user.is_authenticated:
        user_cart = Cart.objects.filter(user=request.user).first()

        if user_cart:
            cart_items = CartItem.objects.filter(cart=user_cart)
            total_price = calculate_cart_total(cart_items)
        else:
            cart_items = []
            total_price = 0

        context = {
            'cart_items': cart_items,
            'total_price': total_price,
        }

        return render(request, 'app/cart2.html', context)
    else:
        return render(request, 'app/cart2.html')

def calculate_cart_total(cart_items):
    total_price = 0

    for item in cart_items:
        product = item.product
        quantity = item.quantity
        item_price = product.discount_price * quantity
        total_price += item_price

    return total_price


def add_to_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id)

    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        quantity = request.POST.get('quantity', 1)

        try:
            quantity = int(quantity)
        except ValueError:
            quantity = 1

        if quantity > product.stock:
            return redirect('product-detail', pk=product_id)

        # Check if the product is already in the cart
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        if not created:
            cart_item_exists = True
        else:
            cart_item_exists = False
            cart_item.quantity = quantity  # Set the initial quantity
            cart_item.save()

        next_url = request.POST.get('next')
        if next_url:
            return redirect(next_url)
        else:
            return redirect('product-detail', pk=product_id)
    else:
        return redirect('login')



def delete_cart_item(request, item_id):
    if request.user.is_authenticated:
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        cart_item.delete()
        next_url = request.POST.get('next')
        if next_url:
            return redirect(next_url)
        else:
            return redirect('cart')

def plus_cart(request):
    if request.method == 'GET':
        prod_id = request.GET.get('prod_id')
        c = CartItem.objects.get(Q(product=prod_id) & Q(cart__user=request.user))
        if c.quantity < c.product.stock:
            c.quantity += 1
            c.save()

        cart_items = CartItem.objects.filter(cart__user=request.user)

        total_price = 0

        for item in cart_items:
            product = item.product
            quantity = item.quantity
            item_price = product.discount_price * quantity
            total_price += item_price


        data = {
            'quantity': c.quantity,
            'amount': total_price,

        }
        if c.quantity == c.product.stock:
            data['out_of_stock'] = True
        else:
            data['out_of_stock'] = False
        print(data['out_of_stock'])

        return JsonResponse(data)

def minus_cart(request):
    if request.method == 'GET':
        print('hai')
        prod_id = request.GET.get('prod_id')
        c = CartItem.objects.get(Q(product=prod_id) & Q(cart__user=request.user))
        if c.quantity > 1:
            c.quantity -= 1
            c.save()

        cart_items = CartItem.objects.filter(cart__user=request.user)

        total_price = 0

        for item in cart_items:
            product = item.product
            quantity = item.quantity
            item_price = product.discount_price * quantity
            total_price += item_price

        data = {
            'quantity': c.quantity,
            'amount': total_price,

        }
        return JsonResponse(data)


class CheckoutView(View):
    def get(self, request):
        if not CartItem.objects.filter(cart__user=request.user).exists():
            messages.error(request, "Your cart is empty. Add items to your cart before checking out.")
            return redirect('cart')
        form = CustomerProfileForm()
        if request.user.is_authenticated:
            address = Customer.objects.filter(user=request.user)
            product_data, final_price = self.get_product_data(request.user)
            product_offer,category_offer = self.available_offers(request.user)
            # print('recieved data-',data)
            context = {
                'form': form,
                'product_data': product_data,
                'final_price': final_price,
                'address': address,
                'product_offer':product_offer,
                'category_offer':category_offer,
            }

            return render(request, 'app/checkout.html', context)

    def post(self, request):
        form = CustomerProfileForm(request.POST)
        if form.is_valid():
            print('hai')
            usr = request.user
            name = form.cleaned_data['name']
            phone_number = form.cleaned_data['phone_number']
            locality = form.cleaned_data['locality']
            city = form.cleaned_data['city']
            state = form.cleaned_data['state']
            pincode = form.cleaned_data['pincode']
            reg = Customer(
                user=usr,
                name=name,
                phone_number=phone_number,
                locality=locality,
                city=city,
                state=state,
                pincode=pincode
            )
            reg.save()
            messages.success(request, 'Congratulations!! Address Updated Successfully')

        product_data, final_price = self.get_product_data(request.user)
        address = Customer.objects.filter(user=request.user)
        product_offer,category_offer = self.available_offers(request.user)

        context = {
            'form': form,
            'product_data': product_data,
            'final_price': final_price,
            'address': address,
            'product_offer':product_offer,
            'category_offer':category_offer,
        }

        return render(request, 'app/checkout.html', context)

    def get_product_data(self, user):
        cart_items = CartItem.objects.filter(cart__user=user)

        product_data = []
        final_price = 0

        for item in cart_items:
            product = item.product
            quantity = item.quantity
            total_price = product.discount_price * quantity
            product_data.append({
                'product': product,
                'quantity': quantity,
                'total_price': total_price,
            })
            final_price += total_price

        return product_data, final_price

    def available_offers(self, user):
        try:
            selected_products = CartItem.objects.filter(cart__user=user)

            if selected_products:
                product_offers = []
                category_offers = []
                for item in selected_products:
                    product_offers.extend(ProductOffer.objects.filter(product=item.product))
                    category_offers.extend(CategoryOffer.objects.filter(category=item.product.category))
                return product_offers,category_offers
            else:
                return None

        except ObjectDoesNotExist as e:
            print(f"Error: {e}")
            return None



def offer_adding(request):
    print('hw')
    t_instance = CheckoutView()
    product_data, final_price = t_instance.get_product_data(request.user)
    # product_offer, category_offer = self.available_offers(request.user)
    if request.method == 'GET':
        print('h2')
        offer_id = request.GET.get('offer_id')
        if offer_id:
            try:
                product_offer = ProductOffer.objects.get(pk=offer_id)
            except ProductOffer.DoesNotExist:
                product_offer = None

            try:
                category_offer = CategoryOffer.objects.get(pk=offer_id)
            except CategoryOffer.DoesNotExist:
                category_offer = None

            if product_offer:
                    discount = min(product_offer.max_discount_amount,(product_offer.product.discount_price * product_offer.discount_percentage) / 100)
                    final_price = final_price - discount

            if category_offer:
                    discount = min(category_offer.max_discount_amount,(product_offer.product.discount_price * category_offer.discount_percentage) / 100)
                    final_price = final_price - discount

    # Return the final price after applying the offer
    data = {
        'final_price': final_price,
        'discount':discount,
    }
    return JsonResponse(data)





from django.shortcuts import render, redirect
from .models import Order, BillingAddress, ShippingAddress, Customer, Cart, OrderItem

# def order_placed(request):
#     if request.method == 'POST':
#         user = request.user
#         billing_address_id = request.POST.get('billing_address_id')
#         shipping_address_id = request.POST.get('shipping_address_id')
#         try:
#             discount_str = request.POST.get('discount')
#             print('dis', discount_str)
#             payment_method = request.POST.get('payment')
#             print('pay-', payment_method)
#
#             if discount_str:
#                 discount = Decimal(discount_str)
#             else:
#                 discount = Decimal('0.00')
#         except (InvalidOperation, TypeError, ValueError):
#             discount = Decimal('0.00')
#         # try:
#         #     discount = Decimal(discount_str)
#         #     print('disc1',discount)
#         # except (InvalidOperation, TypeError, ValueError):
#         #     # Handle the case where the discount_str is not a valid decimal
#         #     discount = Decimal('0.00')
#         #     print('disc2-',discount)
#         try:
#             customer = Customer.objects.get(id=billing_address_id)
#
#             billing_address = BillingAddress(
#                 user=customer.user,
#                 name=customer.name,
#                 locality=customer.locality,
#                 city=customer.city,
#                 pincode=customer.pincode,
#                 state=customer.state,
#                 phone_number=customer.phone_number
#             )
#
#             billing_address.save()
#
#             customer = Customer.objects.get(id=shipping_address_id)
#
#             shipping_address = ShippingAddress(
#                 user=customer.user,
#                 name=customer.name,
#                 locality=customer.locality,
#                 city=customer.city,
#                 pincode=customer.pincode,
#                 state=customer.state,
#                 phone_number=customer.phone_number
#             )
#
#             shipping_address.save()
#
#             cart_items = CartItem.objects.filter(cart__user=user)
#             total_price = sum(item.product.discount_price * item.quantity for item in cart_items)
#
#             if discount != 0:
#                 total_price -= discount
#
#             order = Order(
#                 user=user,
#                 billing_address=billing_address,
#                 shipping_address=shipping_address,
#                 discount=discount,
#                 total_price=total_price,
#                 payment_method=payment_method
#             )
#             try:
#                 order.save()
#                 print('Order saved successfully')
#
#
#                 for cart_item in cart_items:
#                     order_item = OrderItem(
#                         order=order,
#                         product=cart_item.product,
#                         quantity=cart_item.quantity,
#                         price_per_product=cart_item.product.discount_price
#                     )
#                     order_item.save()
#                     print(order_item)
#                     product = cart_item.product
#                     product.stock -= cart_item.quantity
#                     product.save()
#
#                 cart_items.delete()
#             except Exception as e:
#                 print(f'Error saving the order: {str(e)}')
#             return redirect( 'user_orders')
#         except Customer.DoesNotExist:
#             pass
#
#     return redirect('checkout')



def order_placed(request):
    if request.method == 'POST':
        user = request.user
        billing_address_id = request.POST.get('billing_address_id')
        shipping_address_id = request.POST.get('shipping_address_id')

        discount_str = request.POST.get('discount', '0.00')
        print('dis', discount_str)
        payment_method = request.POST.get('payment')
        print('pay-', payment_method)

        try:
            discount = Decimal(discount_str)
        except (InvalidOperation, ValueError):
            discount = Decimal('0.00')

        try:
            customer = Customer.objects.get(id=billing_address_id)

            billing_address = BillingAddress(
                user=customer.user,
                name=customer.name,
                locality=customer.locality,
                city=customer.city,
                pincode=customer.pincode,
                state=customer.state,
                phone_number=customer.phone_number
            )

            billing_address.save()
            print('bill add')

            customer = Customer.objects.get(id=shipping_address_id)

            shipping_address = ShippingAddress(
                user=customer.user,
                name=customer.name,
                locality=customer.locality,
                city=customer.city,
                pincode=customer.pincode,
                state=customer.state,
                phone_number=customer.phone_number
            )

            shipping_address.save()
            print('ship add')

            cart_items = CartItem.objects.filter(cart__user=user)
            total_price = sum(item.product.discount_price * item.quantity for item in cart_items)
            print('tot1',total_price)
            if discount != Decimal('0.00'):
                total_price -= discount
                print('tot2-',total_price)

            order = Order(
                user=user,
                billing_address=billing_address,
                shipping_address=shipping_address,
                discount=discount,
                total_price=total_price,
                payment_method=payment_method
            )
            print(user,billing_address,shipping_address,discount,total_price,payment_method)
            print(type(discount))
            print(order)

            try:
                order.save()
                print('Order saved successfully')

                for cart_item in cart_items:
                    order_item = OrderItem(
                        order=order,
                        product=cart_item.product,
                        quantity=cart_item.quantity,
                        price_per_product=cart_item.product.discount_price
                    )
                    order_item.save()
                    print(order_item)

                    product = cart_item.product
                    product.stock -= cart_item.quantity
                    product.save()

                cart_items.delete()
            except Exception as e:
                print(f'Error saving the order: {str(e)}')
                return redirect('checkout')
            return redirect('user_orders')
        except Customer.DoesNotExist:
            pass

    return redirect('checkout')




def user_orders(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('orderitem_set__product').order_by('-ordered_date')


    paginator = Paginator(orders, 5)
    page_number = request.GET.get('page')
    orders_page = paginator.get_page(page_number)
    total_pages = paginator.num_pages
    page_range = range(orders_page.number, min(orders_page.number + 3, total_pages + 1))

    context = {
        'lastpage': total_pages,
        'page_range': page_range,
        'orders': orders_page,
    }

    return render(request, 'app/user_orders.html', context)




def cancel_order(request, order_id):
    try:
        order = Order.objects.get(id=order_id)


        if order.user == request.user:
            order.order_status = 'Cancelled'
            order.save()

            for order_item in order.orderitem_set.all():
                product = order_item.product
                product.stock += order_item.quantity
                product.save()

            return redirect('user_orders')
        else:
            return HttpResponse("You are not authorized to cancel this order.")
    except Order.DoesNotExist:
        return HttpResponse("Order not found.")


def admin_orders(request):
    search_query = request.GET.get('search', '')

    # orders = Order.objects.filter(username__icontains=search_query)
    orders = Order.objects.filter(Q(username__icontains=search_query) | Q(orderitem__product__title__icontains=search_query)).order_by('-ordered_date')

    paginator = Paginator(orders, 5)
    page_number = request.GET.get('page')
    orders_page = paginator.get_page(page_number)
    total_pages = paginator.num_pages
    page_range = range(orders_page.number, min(orders_page.number + 3, total_pages + 1))

    context = {
        'lastpage' : total_pages,
        'page_range': page_range,
        'orders': orders_page,
    }

    return render(request, 'app/admin_orders.html', context)

def admin_edit_order_status(request, order_id):
    if request.method == 'POST':
        try:
            order = Order.objects.get(id=order_id)
            new_status = request.POST.get('order_status')

            order.order_status = new_status
            order.save()

            messages.success(request, f"Order status for Order ID {order_id} updated to {new_status}.")
        except Order.DoesNotExist:
            messages.error(request, f"Order with ID {order_id} does not exist.")

    return redirect(reverse('admin_orders'))


def order_details(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    return render(request, 'app/order_details.html', {'order': order})

# def cancel_order(request, order_id):
#     order = get_object_or_404(Order, id=order_id)
#
#     if request.method == 'POST':
#         order.order_status = 'Cancelled'
#         order.save()
#
#         return redirect('user_orders')
#
#     return render(request, 'app/order_details.html', order_id=order.id)

def generate_pdf(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    template_path = 'pdf_convert/invoice.html'
    context = {'order':order}
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="report.pdf"'
    template = get_template(template_path)
    html = template.render(context)

    pisa_status = pisa.CreatePDF(
       html, dest=response)
    if pisa_status.err:
       return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response

    # return render(request, 'pdf_convert/invoice.html',{ 'order':order})



@login_required
def submit_product_review(request, product_id):
    product = Product.objects.get(pk=product_id)

    has_purchased = OrderItem.objects.filter(order__user=request.user, product=product).exists()

    if has_purchased:
        if request.method == 'POST':
            review_text = request.POST.get('review')
            rating = request.POST.get('rating')

            review, created = Review.objects.get_or_create(user=request.user, product=product,defaults={'text': review_text, 'rating': rating})
            if not created:
                review.text = review_text
                review.rating = rating
                review.save()


        return redirect('product-detail', pk=product_id)
    context = {
        'product': product,
    }
    return render(request, 'app/productdetails.html', context)


def create_product_offer(request):
    if request.method == 'POST':
        form = ProductOfferForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('product_offer_list')
    else:
        form = ProductOfferForm()

    return render(request, 'offer/create_product_offer.html', {'form': form})


def product_offer_list(request):
    product_offers = ProductOffer.objects.all()
    return render(request, 'offer/product_offer_list.html', {'product_offers': product_offers})

def create_category_offer(request):
    if request.method == 'POST':
        form = CategoryOfferForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('category_offer_list')
    else:
        form = CategoryOfferForm()

    return render(request, 'offer/create_category_offer.html', {'form': form})


def category_offer_list(request):
    category_offers = CategoryOffer.objects.all()
    return render(request, 'offer/category_offer_list.html', {'category_offers': category_offers})

def create_referral_offer(request):
    if request.method == 'POST':
        form = ReferralOfferForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('referral_offer_list')
    else:
        form = ReferralOfferForm()

    return render(request, 'offer/create_referral_offer.html', {'form': form})


def referral_offer_list(request):
    referral_offers = ReferralOffer.objects.all()
    return render(request, 'offer/referral_offer_list.html', {'referral_offers': referral_offers})

def generate_referral_code(username):
    return f"{username}@payfortech"




# def available_offers(request):
#     try:
#         print('hai')
#         selected_product = CartItem.objects.get(cart__user=request.user)
#         print(selected_product)
#
#         product_offers = ProductOffer.objects.filter(product=selected_product.product)
#         # category_offers = CategoryOffer.objects.filter(category=selected_product.category)
#         print(product_offers, 'haa')
#         # print('hai2', category_offers)
#
#         context = {
#             'product_offers': product_offers,
#             # 'category_offers': category_offers,
#         }
#
#         return render(request, 'app/available_offers.html', context)
#
#     except ObjectDoesNotExist as e:
#         print(f"Error: {e}")
#         return render(request, 'offer/error_page.html', {'error_message': str(e)})
#     except Exception as e:
#         print(f"Error: {e}")
#         return render(request, 'offer/error_page.html', {'error_message': str(e)})


# def available_offers(request):
#     print('hai')
#     try:
#         selected_product = CartItem.objects.get(cart__user=request.user)
#         print(selected_product)
#         product_offers = ProductOffer.objects.filter(product=selected_product.product)
#         print(product_offers)
#         context = {
#             'product_offers': product_offers,
#         }
#         return render(request, 'checkout.html', context)
#     except ObjectDoesNotExist as e:
#         print(f"Error: {e}")
#         return render(request, 'offer/error_page.html', {'error_message': str(e)})





def monthly_sales_report(request):
    orders = Order.objects.annotate(month=ExtractMonth('ordered_date')).values('month').annotate(count=Count('id')).values('month','count')
    month_number = []
    total_order = []
    for d in orders:
        month_number.append(calendar.month_name[d['month']])
        total_order.append(d['count'])

    print(month_number,total_order)
    context ={
        'month_number':month_number,
        'total_order':total_order
    }
    return render(request, 'report/monthly_sales_report.html', context)


def daily_sales_report(request):
    form = MonthYearForm()
    month = 1
    year = 2023
    if request.method == 'POST':
        form = MonthYearForm(request.POST)
        if form.is_valid():
            month = form.cleaned_data['month']
            year = form.cleaned_data['year']
        else:
            current_date = datetime.now()
            month = current_date.month
            year = current_date.year
    else:
        form = MonthYearForm(initial={'month': 1, 'year': 2023})

    orders = Order.objects.filter(
        ordered_date__month=month,
        ordered_date__year=year
    ).annotate(day=ExtractDay('ordered_date')).values('day').annotate(count=Count('id')).values('day', 'count')

    day_number = []
    total_order = []

    for d in orders:
        day_number.append(d['day'])
        total_order.append(d['count'])

    context = {
        'day_number': day_number,
        'total_order': total_order,
        'selected_month': int(month),
        'selected_year': int(year),
        'form': form,
    }

    return render(request, 'report/daily_sales_report.html', context)

def yearly_sales_report(request):
    orders = Order.objects.annotate(year=ExtractYear('ordered_date')).values('year').annotate(count=Count('id')).values('year','count')
    year_number = []
    total_order = []
    for d in orders:
        year_number.append(d['year'])
        total_order.append(d['count'])

    print(year_number,total_order)
    context ={
        'year_number':year_number,
        'total_order':total_order
    }
    return render(request, 'report/yearly_sales_report.html', context)


from io import BytesIO
import openpyxl
import datetime
from reportlab.lib.pagesizes import letter,landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.platypus import Paragraph
from reportlab.platypus.tables import Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet


def generate_pdf_report(data):
    buffer = BytesIO()
    pdf = SimpleDocTemplate(buffer, pagesize=landscape(letter))
    elements = []

    title = Paragraph("Sales Report", getSampleStyleSheet()['Title'])
    elements.append(title)

    # table_data = [data[0]]
    # table_data.extend(data[1:])
    formatted_data = [data[0]]
    col_widths = [60, 80, 60, 80, 140, 80, 80, 80]

    for row in data[1:]:
        formatted_row = []
        for i, cell in enumerate(row):
            if i == 1 and isinstance(cell, datetime.datetime):
                # Format date to display only date, month, year
                formatted_date = cell.strftime("%d-%b-%Y")
                formatted_row.append(formatted_date)
            else:
                formatted_row.append(cell)
        formatted_data.append(formatted_row)

    table = Table(formatted_data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    elements.append(table)
    pdf.build(elements)
    buffer.seek(0)
    return buffer

def generate_excel_report(data):
    workbook = openpyxl.Workbook()
    sheet = workbook.active

    for row in data:
        cleaned_row = []
        for cell in row:
            if isinstance(cell, datetime.datetime):
                cell = cell.replace(tzinfo=None)
            cleaned_row.append(cell)
        sheet.append(cleaned_row)

    excel_file = BytesIO()
    workbook.save(excel_file)
    excel_file.seek(0)
    return excel_file

def generate_sales_report(request):
    if request.method == 'POST':
        report_format = request.POST.get('report_format')
        orders = Order.objects.all()
        report_data = [
            ['Order ID', 'Ordered Date', 'Username', 'Order Status', 'Product', 'Price per Product', 'Quantity',
             'Sub Total']]

        for order in orders:
            for item in OrderItem.objects.filter(order=order):
                report_data.append([order.id, order.ordered_date, order.username, order.get_order_status_display(),
                                    item.product.title, item.price_per_product, item.quantity,
                                    item.total_price_product])

        if report_format == 'pdf':
            # Generate and return the PDF report
            pdf_file = generate_pdf_report(report_data)  # Replace with your data
            response = HttpResponse(pdf_file, content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="sales_report.pdf"'
            return response

        elif report_format == 'excel':
            # Generate and return the Excel report
            excel_file = generate_excel_report(report_data)  # Replace with your data
            response = HttpResponse(excel_file, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename="sales_report.xlsx"'
            return response

    return render(request, 'pdf_convert/generate_sales_report.html')




def sales_report(request):

    return render(request, 'pdf_convert/generate_sales_report.html',)

from django.http import JsonResponse

def clear_filter(request):
    products = Product.objects.all()
    # You can filter and serialize the products as needed
    data = [{'title': product.title, 'selling_price': product.selling_price} for product in products]
    return JsonResponse(data, safe=False)
