from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxLengthValidator,MinValueValidator, RegexValidator



STATE_CHOICES = (
    ('AP', 'Andhra Pradesh'),
    ('AR', 'Arunachal Pradesh'),
    ('AS', 'Assam'),
    ('BR', 'Bihar'),
    ('CG', 'Chhattisgarh'),
    ('GA', 'Goa'),
    ('GJ', 'Gujarat'),
    ('HR', 'Haryana'),
    ('HP', 'Himachal Pradesh'),
    ('JH', 'Jharkhand'),
    ('KA', 'Karnataka'),
    ('KL', 'Kerala'),
    ('MP', 'Madhya Pradesh'),
    ('MH', 'Maharashtra'),
    ('MN', 'Manipur'),
    ('ML', 'Meghalaya'),
    ('MZ', 'Mizoram'),
    ('NL', 'Nagaland'),
    ('OD', 'Odisha'),
    ('PB', 'Punjab'),
    ('RJ', 'Rajasthan'),
    ('SK', 'Sikkim'),
    ('TN', 'Tamil Nadu'),
    ('TS', 'Telangana'),
    ('TR', 'Tripura'),
    ('UP', 'Uttar Pradesh'),
    ('UK', 'Uttarakhand'),
    ('WB', 'West Bengal'),
    ('AN', 'Andaman and Nicobar Islands'),
    ('CH', 'Chandigarh'),
    ('DN', 'Dadra and Nagar Haveli and Daman and Diu'),
    ('DL', 'Delhi'),
    ('JK', 'Jammu and Kashmir'),
    ('LA', 'Ladakh'),
    ('LD', 'Lakshadweep'),
    ('PY', 'Puducherry'),
)

# address table
class Customer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    locality = models.CharField(max_length=200)
    city = models.CharField(max_length=50)
    pincode = models.IntegerField()
    state = models.CharField(choices=STATE_CHOICES,max_length=50)

    # Add a phone_number field with digit-only validation
    phone_regex = RegexValidator(
        regex=r'^\d{10}$',  # Matches a 10-digit number
        message="Phone number must be 10 digits long."
    )
    phone_number = models.CharField(validators=[phone_regex], max_length=10)


    def __str__(self):
        return str(self.id)







class ProductImage(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='product_images/')

    def __str__(self):
        return str(self.product) + " - " + str(self.id)

unique_case_insensitive_validator = RegexValidator(
    r'^[a-zA-Z0-9_]*$',
    message="Name must be unique and case-sensitive.",
    flags=models.UniqueConstraint
)


class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    title = models.CharField(max_length=100)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    details = models.TextField(max_length=255, default='No details available')
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    stock = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.title



class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"Cart for {self.user.username}"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.title}"

class OrderPlaced(models.Model):
    pass

class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.user.username} - {self.product.title}'





class BillingAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=200)
    locality = models.CharField(max_length=200)
    city = models.CharField(max_length=50)
    pincode = models.IntegerField()
    state = models.CharField(choices=STATE_CHOICES,max_length=50)

    phone_regex = RegexValidator(
        regex=r'^\d{10}$',  # Matches a 10-digit number
        message="Phone number must be 10 digits long."
    )
    phone_number = models.CharField(validators=[phone_regex], max_length=10)


    def __str__(self):
        return str(self.id)

class ShippingAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=200)
    locality = models.CharField(max_length=200)
    city = models.CharField(max_length=50)
    pincode = models.IntegerField()
    state = models.CharField(choices=STATE_CHOICES,max_length=50)

    phone_regex = RegexValidator(
        regex=r'^\d{10}$',  # Matches a 10-digit number
        message="Phone number must be 10 digits long."
    )
    phone_number = models.CharField(validators=[phone_regex], max_length=10)


    def __str__(self):
        return str(self.id)

class Order(models.Model):
    ORDER_STATUS_CHOICES = (
        ('Processing', 'Processing'),
        ('Confirmed', 'Confirmed'),
        ('Shipped', 'Shipped'),
        ('Out for Delivery', 'Out for Delivery'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    )

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    billing_address = models.OneToOneField(BillingAddress, on_delete=models.CASCADE, null=True)
    shipping_address = models.OneToOneField(ShippingAddress, on_delete=models.CASCADE, null=True)
    order_status = models.CharField(max_length=100, choices=ORDER_STATUS_CHOICES, default='Processing')
    ordered_date = models.DateTimeField(auto_now_add=True)
    username = models.CharField(max_length=150, blank=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Order for {self.username}"

    def save(self, *args, **kwargs):
        if self.user:
            self.username = self.user.username
        super(Order, self).save(*args, **kwargs)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField(default=1)
    price_per_product = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product.title} in Order {self.order.id}"