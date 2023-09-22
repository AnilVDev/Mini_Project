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


class ProductView(View):
    def get(self, request):
        camera = Product.objects.filter(Q(category__name__icontains='camera'))
        smartwatch = Product.objects.filter(Q(category__name__icontains='smart watch'))
        categories = Product.objects.values_list('category__name', flat=True).distinct()

        context = {
            'camera': camera,
            'smartwatch': smartwatch,
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
                        password=user_data['password'],  # Replace with your password hashing logic
                    )
                    del request.session['temp_user_data']
                    # Valid OTP
                    del request.session['registration_otp']
                    del request.session['otp_attempts']
                    messages.success(request, 'OTP verified successfully. Registration complete!')
                    # Perform your user registration logic here
                    return redirect('login')  # Redirect to login page or any other desired page
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
        return render(request, 'app/profile.html',{'form':form,'active':'bg-danger'})
@method_decorator(staff_member_required, name='dispatch')
def add_product_with_images(request):
    if request.method == 'POST':
        product_form = ProductForm(request.POST)
        image_formset = ProductImageFormSet(request.POST, request.FILES, prefix='images')

        if product_form.is_valid() and image_formset.is_valid():
            # Save the product
            product = product_form.save()

            # Associate each image with the product
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
        # Use the AuthenticationForm to validate the login data
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            # Get the user from the form
            user = form.get_user()

            # Check if the user is a superuser (admin)
            if user.is_superuser:
                login(request)  # Log in the user
                return redirect('admin_home')
            else:
                errors = 'You are not an admin. Please use User login.'


    else:
        # Display the login form
        form = AuthenticationForm(request)

    return render(request, 'app/admin_login.html', {'form': form, 'errors': errors})



@staff_member_required
def admin_home(request):
    return render(request,'app/admin_home.html')

@staff_member_required
def user_list(request):
    users = User.objects.all()
    return render(request, 'app/user_list.html', {'users': users})

@method_decorator(staff_member_required, name='dispatch')
class DeleteUserView(View):
    def get(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        user.delete()
        return redirect('user_list')
@method_decorator(staff_member_required, name='dispatch')
class ProductListView(ListView):
    model = Product
    template_name = 'app/product_list.html'
    context_object_name = 'products'

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




# @staff_member_required
# def add_product_images(request):
#     if request.method == 'POST':
#         formset = ProductImageFormSet(request.POST, request.FILES, queryset=ProductImage.objects.none())
#         if formset.is_valid():
#             formset.save()
#             return redirect('product_list')  # Redirect to the product list page or any other appropriate page
#     else:
#         formset = ProductImageFormSet(queryset=ProductImage.objects.none())
#
#     return render(request, 'app/add_image_to_product.html', {'formset': formset})

@staff_member_required
def add_product_images(request, product_id):
    product = Product.objects.get(pk=product_id)

    if request.method == 'POST':
        formset = ProductImageFormSet(request.POST, request.FILES, queryset=ProductImage.objects.none())
        if formset.is_valid():
            for form in formset:
                if form.cleaned_data:
                    image = form.save(commit=False)
                    image.product = product
                    image.save()
            return redirect('product_list')  # Redirect to the product list page or any other appropriate page
    else:
        formset = ProductImageFormSet(queryset=ProductImage.objects.none())

    return render(request, 'app/add_image_to_product.html', {'formset': formset, 'product': product})

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
def category_list_and_add(request):
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

    return render(request, 'app/category_list_and_add.html', {'categories': categories, 'form': form})

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
    return render(request, 'app/brand_list_and_add.html', {'brands': brands, 'form': form})

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