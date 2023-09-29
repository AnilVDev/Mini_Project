from django.shortcuts import render,redirect,get_object_or_404
from django.views import View
from .models import Customer,Cart,Product,OrderPlaced,ProductImage,Category,Brand
from .forms import CustomerRegistrationForm,CustomerProfileForm,ProductForm, CustomAdminLoginForm, MyPasswordChangeForm, OTPVerificationForm, ProductImageFormSet, ProductImageForm,CategoryForm,BrandForm
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


class ProductView(View):
    def get(self, request):
        camera = Product.objects.filter(Q(category__name__icontains='camera'))
        smartwatch = Product.objects.filter(Q(category__name__icontains='smart watch'))
        headphone = Product.objects.filter(Q(category__name__icontains='headphone'))
        speaker = Product.objects.filter(Q(category__name__icontains='speaker'))
        categories = Product.objects.values_list('category__name', flat=True).distinct()

        context = {
            'camera': camera,
            'smartwatch': smartwatch,
            'headphone':headphone,
            'speaker':speaker,
            'categories': categories,

        }
        return render(request, 'app/index.html', context)


class ProductDetailView(View):
    def get(self, request,pk):
        product = Product.objects.get(pk=pk)
        return render(request, 'app/productdetails.html', {'product':product})

def add_to_cart(request):
 return render(request, 'app/addtocart.html')

def buy_now(request):
 return render(request, 'app/buynow.html')

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


def orders(request):
 return render(request, 'app/orders.html')



def mobile(request):
 return render(request, 'app/mobile.html')

def login(request):
 return render(request, 'app/login.html')





def checkout(request):
 return render(request, 'app/checkout.html')

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
                    # Valid OTP
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
        return render(request, 'app/profile.html', {'form':form, 'active':'bg-danger'})

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
            messages.success(request, 'Congratulations!! Profile Updated Successfully')

        form = CustomerProfileForm()
        return render(request, 'app/profile.html',{'form':form,'active':'bg-danger'})
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

            return redirect('product_list')  # Redirect to a success page or product list
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

    return render(request,'app/admin_home.html')

@staff_member_required
def user_list(request):
    query = request.GET.get('q', '')
    if query:
        users = User.objects.filter( Q(username__icontains=query) | Q(email__icontains=query))
    else:
        users = User.objects.all()

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
        # Optionally, you can add a success message
        messages.success(request, 'Category deleted successfully.')
    except Category.DoesNotExist:
        messages.error(request, 'Category not found.')

    # Redirect to the page where you list categories
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
        # Optionally, you can add a success message
        messages.success(request, 'Brand deleted successfully.')
    except Brand.DoesNotExist:
        messages.error(request, 'Brand not found.')

    # Redirect to the page where you list categories
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

    if category != 'All Categories':
        products = Product.objects.filter(category__name=category)
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

    products_per_page = 3

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
    }

    return render(request, 'app/product_listing.html', context)
