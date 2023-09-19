from django.shortcuts import render,redirect
from django.views import View
from .models import Customer,Cart,Product,OrderPlaced,ProductImage,Category
from .forms import CustomerRegistrationForm,CustomerProfileForm,ProductForm, ProductImageForm, CustomAdminLoginForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.forms import modelformset_factory
from .forms import MyPasswordChangeForm
from django.db.models import Q
from django.contrib.auth import views as auth_views
from django.urls import reverse
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.views import LoginView
from django.contrib.auth.forms import AuthenticationForm
from django.views.decorators.cache import never_cache
from django.contrib.auth import logout

class ProductView(View):
    def get(self, request):
        camera = Product.objects.filter(Q(category__name__icontains='camera'))
        watch = Product.objects.filter(Q(category__name__icontains='watch'))
        categories = Product.objects.values_list('category__name', flat=True).distinct()

        context = {
            'camera': camera,
            'watch': watch,
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
          return render(request, 'app/customerregistration.html', {'form':form})

     def post(self, request):
      form = CustomerRegistrationForm(request.POST)
      if form.is_valid():
         messages.success(request, 'Registered Successfully')
         form.save()
      form = CustomerRegistrationForm()
      return render(request, 'app/customerregistration.html', {'form': form})

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



@never_cache
def admin_home(request):
    # if 'username' in request.session:
    #     username = request.session['username']
    #     user = Custom_user.objects.get(username = username)
    #
    #     if user.is_superuser:
    #         search = request.POST.get('search')
    #
    #         if search:
    #             userDatas = Custom_user.objects.filter(username__istartswith = search)
    #         else:
    #             userDatas = Custom_user.objects.filter(is_superuser = False)
    #         return render(request, 'admin_Home.html', {'datas': userDatas})
    return render(request,'app/admin_home.html')


