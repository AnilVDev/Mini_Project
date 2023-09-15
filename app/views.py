from django.shortcuts import render
from django.views import View
from .models import Customer,Cart,Product,OrderPlaced
from .forms import CustomerRegistrationForm,CustomerProfileForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

def home(request):
 return render(request, 'app/home.html')

def product_detail(request):
 return render(request, 'app/productdetail.html')

def add_to_cart(request):
 return render(request, 'app/addtocart.html')

def buy_now(request):
 return render(request, 'app/buynow.html')

@login_required
def address(request):
 add = Customer.objects.filter(user=request.user)
 return render(request, 'app/address.html', {'add':add,'active':'btn-primary'})

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
      return render(request, 'app/customerregistration.html', {'form': form})

@method_decorator(login_required, name='dispatch')
class ProfileView(View):
    def get(self, request):
        form = CustomerProfileForm()
        return render(request, 'app/profile.html', {'form':form, 'active':'btn-primary'})

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
        return render(request, 'app/profile.html',{'form':form,'active':'btn-primary'})