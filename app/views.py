import random
from django.shortcuts import render,redirect,get_object_or_404
from django.views import View
from .models import Customer,Cart,Product,OrderPlaced,ProductImage,Category,Brand,Wishlist,CartItem,Order,OrderItem,BillingAddress,ShippingAddress,Review,ProductOffer,ReferralOffer,CategoryOffer

from .forms import CustomerRegistrationForm,CustomerProfileForm,ProductForm, CustomAdminLoginForm, MyPasswordChangeForm, OTPVerificationForm, ProductImageFormSet, ProductImageForm,CategoryForm,BrandForm,UserProfileForm,ProductOfferForm,ReferralOfferForm,CategoryOfferForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.forms import modelformset_factory
from django.db.models import Q
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


def product_listing(request, category):
    print('from-',category)
    selected_category = request.GET.get('category', 'All Categories')
    print('sel-',selected_category)
    search_query = request.GET.get('search_query', '')
    print(search_query)
    selected_brands = request.GET.getlist('brand')
    print(selected_brands)
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    categories = Category.objects.all()
    brands = Brand.objects.all()

    if category != 'All Categories' and selected_category == 'All Categories':
        products = Product.objects.filter(category__name=category)
        print('from all category',products)
    else:
        if selected_category == 'All Categories':
            products = Product.objects.all()
            print('all-',products,category)
        else:
            products = Product.objects.filter(category__name=selected_category)
            print('else-',products)
    print(category,products)

    if search_query:
        products = products.filter(Q(title__icontains=search_query) | Q(description__icontains=search_query))
    print('search query-',products)

    if selected_brands:
        print(products)
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
        'category': category,
        'selected_category': selected_category,
        'search_query': search_query,
        'selected_brands': selected_brands,
        'min_price': min_price,
        'max_price': max_price,
        'categories': categories,
        'brands': brands,
        'page_range': page_range,
        'products': products_page,
        # 'sort_by_price': sort_by_price,

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

            context = {
                'form': form,
                'product_data': product_data,
                'final_price': final_price,
                'address': address,
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

        context = {
            'form': form,
            'product_data': product_data,
            'final_price': final_price,
            'address': address,
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



from django.shortcuts import render, redirect
from .models import Order, BillingAddress, ShippingAddress, Customer, Cart, OrderItem

def order_placed(request):
    if request.method == 'POST':
        user = request.user
        billing_address_id = request.POST.get('billing_address_id')
        shipping_address_id = request.POST.get('shipping_address_id')

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

            cart_items = CartItem.objects.filter(cart__user=user)
            total_price = sum(item.product.discount_price * item.quantity for item in cart_items)


            order = Order(
                user=user,
                billing_address=billing_address,
                shipping_address=shipping_address,
                total_price=total_price,
            )
            order.save()
            print(order)

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

            return render(request, 'user_orders')
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
    product = Product.objects.get(pk=product_id)  # Replace Product with your actual product model

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