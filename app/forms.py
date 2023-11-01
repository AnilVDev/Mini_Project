from django import forms
from django.contrib.auth.forms import UserCreationForm,AuthenticationForm,UsernameField, PasswordChangeForm, PasswordResetForm, SetPasswordForm,UserChangeForm
from django.contrib.auth.models import User
from django.utils.translation import gettext,gettext_lazy as _
from django.contrib.auth import password_validation
from .models import Customer,Product, ProductImage,Category,Brand,ProductOffer,CategoryOffer,ReferralOffer
from django.core.validators import RegexValidator
from django.forms import modelformset_factory
import random


class CustomerRegistrationForm(UserCreationForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput(attrs={'class':'form-control'}))
    password2 = forms.CharField(label='Confirm Password (again)', widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    email = forms.CharField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))

    def generate_otp(self):
        # Generate a random OTP
        return str(random.randint(100000, 999999))

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        labels = {'email': 'Email'}
        widgets = {'username': forms.TextInput(attrs={'class':'form-control'})}

class UserProfileForm(UserChangeForm):
    username = forms.CharField(label='Username', widget=forms.TextInput(attrs={'class': 'form-control', 'style': 'width: 20rem;'}))
    first_name = forms.CharField(label='First Name', widget=forms.TextInput(attrs={'class': 'form-control', 'style': 'width: 20rem;'}))
    last_name = forms.CharField(label='Last Name', widget=forms.TextInput(attrs={'class': 'form-control', 'style': 'width: 20rem;'}))
    email = forms.EmailField(label='Email', widget=forms.TextInput(attrs={'class': 'form-control', 'style': 'width: 20rem;'}))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']


class MyPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(label=_("Old Password"),strip=False, widget=forms.PasswordInput(attrs={'autocomplete': 'current-password', 'autofocus':True, 'class': 'form-control'}))
    new_password1 = forms.CharField(label=_("New Password"), strip=False, widget=forms.PasswordInput(
        attrs={'autocomplete': 'new-password', 'class': 'form-control'}), help_text=password_validation.password_validators_help_text_html())
    new_password2 = forms.CharField(label=_("Confirm New Password"), strip=False, widget=forms.PasswordInput(
        attrs={'autocomplete': 'new-password', 'class': 'form-control'}))

class MyPasswordResetForm(PasswordResetForm):
    email =  forms.EmailField(label=_("Email"), max_length=254,widget=forms.EmailInput(attrs={'autocomplete':'email','class':'form-control'}))

class MySetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(label=_("New Password"), strip=False, widget=forms.PasswordInput(
        attrs={'autocomplete': 'new-password', 'class': 'form-control'}),help_text=password_validation.password_validators_help_text_html())
    new_password2 = forms.CharField(label=_("Confirm New Password"), strip=False, widget=forms.PasswordInput(
        attrs={'autocomplete': 'new-password', 'class': 'form-control'}))


class CustomerProfileForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name','phone_number', 'locality', 'city', 'state', 'pincode']
        widgets = {'name':forms.TextInput(attrs={'class':'form-control'}),
                   'phone_number':forms.NumberInput(attrs={'class':'form-control'}),
                   'locality':forms.TextInput(attrs={'class':'form-control'}),
                   'city':forms.TextInput(attrs={'class':'form-control'}),
                   'state':forms.Select(attrs={'class':'form-control'}),
                   'pincode':forms.NumberInput(attrs={'class':'form-control'}),
                   }

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'selling_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'discount_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'details': forms.TextInput(attrs={'class': 'form-control'}),
            'brand': forms.Select(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
        }

class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ['image']


ProductImageFormSet = modelformset_factory(ProductImage, form=ProductImageForm, extra=4)


class CustomAdminLoginForm(AuthenticationForm):
    username = UsernameField(widget=forms.TextInput(attrs={'autofocus': True, 'class': 'form-control'}))
    password = forms.CharField(label=_("Password"), strip=False, widget=forms.PasswordInput(attrs={'autocomplete': 'current-password', 'class': 'form-control'}))

class OTPVerificationForm(forms.Form):
    otp = forms.CharField(label=_("OTP"), max_length=6, widget=forms.TextInput(attrs={'autocomplete': 'off', 'class' : 'form-control'}))


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name','is_available']

class BrandForm(forms.ModelForm):
    class Meta:
        model = Brand
        fields = ['name','is_available']


class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

class ProductOfferForm(forms.ModelForm):
    class Meta:
        model = ProductOffer
        fields = '__all__'
        widgets = {
            'product': forms.Select(attrs={'class': 'form-control','style': 'width: 25rem;'}),
            'discount_percentage': forms.NumberInput(attrs={'class': 'form-control','style': 'width: 25rem;'}),
            'max_discount_amount': forms.NumberInput(attrs={'class': 'form-control','style': 'width: 25rem;'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date','style': 'width: 25rem;'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control','type': 'date','style': 'width: 25rem;'}),
            'conditions': forms.Textarea(attrs={'class': 'form-control','style': 'width: 25rem;'}),
        }

class CategoryOfferForm(forms.ModelForm):
    class Meta:
        model = CategoryOffer
        fields = '__all__'
        widgets = {
            'category': forms.Select(attrs={'class': 'form-control', 'style': 'width: 25rem;'}),
            'discount_percentage': forms.NumberInput(attrs={'class': 'form-control', 'style': 'width: 25rem;'}),
            'max_discount_amount': forms.NumberInput(attrs={'class': 'form-control', 'style': 'width: 25rem;'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'style': 'width: 25rem;'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'style': 'width: 25rem;'}),
            'conditions': forms.Textarea(attrs={'class': 'form-control', 'style': 'width: 25rem;'}),
        }

class ReferralOfferForm(forms.ModelForm):
    class Meta:
        model = ReferralOffer
        fields = '__all__'
        widgets = {
            'referrer': forms.Select(attrs={'class': 'form-control', 'style': 'width: 25rem;'}),
            'referral_code': forms.TextInput(attrs={'class': 'form-control', 'style': 'width: 25rem;'}),
            'reward': forms.NumberInput(attrs={'class': 'form-control', 'style': 'width: 25rem;'}),
            'used_by': forms.Select(attrs={'class': 'form-control', 'style': 'width: 25rem;'}),
            'created_at': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'style': 'width: 25rem;'}),
        }


class MonthYearForm(forms.Form):
    month = forms.ChoiceField(
        choices=[
            (1, 'January'),
            (2, 'February'),
            (3, 'March'),
            (4, 'April'),
            (5, 'May'),
            (6, 'June'),
            (7, 'July'),
            (8, 'August'),
            (9, 'September'),
            (10, 'October'),
            (11, 'November'),
            (12, 'December')
        ],
        label='Month',
        widget=forms.Select(attrs={'class': 'form-control', 'style': 'width: 20rem;'})
    )
    year = forms.ChoiceField(
        choices=[(year, year) for year in range(2022, 2030)],  # Customize the range as needed
        label='Year',
        widget=forms.Select(attrs={'class': 'form-control', 'style': 'width: 20rem;'})
    )
