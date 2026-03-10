from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(blank=True)
    ROLE_CHOICES = (
        ('buyer', 'Buyer'),
        ('seller', 'Seller'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='buyer')

    def __str__(self):
        return f"{self.username}"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(
            username=instance.username,
            defaults={'email': instance.email}
        )

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    profile, created = Profile.objects.get_or_create(username=instance.username)
    profile.email = instance.email
    profile.save()

class StoreFront(models.Model):
    seller_username = models.CharField(max_length=150, unique=True)
    store_name = models.CharField(max_length=200)
    store_logo = models.ImageField(upload_to='store_logos/', blank=True, null=True)
    banner_image = models.ImageField(upload_to='store_banners/', blank=True, null=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.store_name

class Category(models.Model):
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, default='fa-box')
    seller_username = models.CharField(max_length=150, blank=True, null=True)
    seller_email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    GENDER_CHOICES = (
        ('All',   'All'),
        ('Men',   'Men'),
        ('Women', 'Women'),
        ('Kids',  'Kids'),
    )
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='All')
    stock_count = models.PositiveIntegerField(default=10)
    total_sales = models.PositiveIntegerField(default=0)
    size = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    store = models.ForeignKey(StoreFront, on_delete=models.CASCADE, null=True, blank=True, related_name='products')
    seller_username = models.CharField(max_length=150, blank=True, null=True)
    seller_email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return self.name

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')

    def __str__(self):
        return f"Image for {self.product.name}"

    @property
    def average_rating(self):
        reviews = self.reviews.all()
        if reviews.exists():
            return sum(r.rating for r in reviews) / reviews.count()
        return 0

class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    size = models.CharField(max_length=50, blank=True, null=True)
    color = models.CharField(max_length=50, blank=True, null=True)
    stock_count = models.PositiveIntegerField(default=0)
    extra_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.product.name} - Size: {self.size}, Color: {self.color}"

class Coupon(models.Model):
    seller_username = models.CharField(max_length=150, blank=True, null=True, help_text="Leave blank for a global coupon")
    code = models.CharField(max_length=50, unique=True)
    discount_percentage = models.PositiveIntegerField(help_text='Percentage value (1-100)')
    active = models.BooleanField(default=True)
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_to = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.code

class Cart(models.Model):
    username = models.CharField(max_length=150, unique=True, null=True)
    email = models.EmailField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart for {self.username}"

    @property
    def total_price(self):
        return sum(item.total_price for item in self.cartitem_set.all())

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    selected_size = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        size_info = f" ({self.selected_size})" if self.selected_size else ""
        return f"{self.quantity} x {self.product.name}{size_info}"

    @property
    def total_price(self):
        return self.product.price * self.quantity

class ShippingAddress(models.Model):
    username = models.CharField(max_length=150, blank=True)
    email = models.EmailField(blank=True)
    full_name = models.CharField(max_length=200)
    address_line_1 = models.CharField(max_length=200)
    address_line_2 = models.CharField(max_length=200, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    phone_number = models.CharField(max_length=15)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.full_name}, {self.city}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

class UserAddress(models.Model):
    username = models.CharField(max_length=150)
    email = models.EmailField(blank=True)
    full_name = models.CharField(max_length=200)
    address_line_1 = models.CharField(max_length=200)
    address_line_2 = models.CharField(max_length=200, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    phone_number = models.CharField(max_length=15)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.full_name} ({self.city})"

class Order(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Returned', 'Returned'),
        ('Cancelled', 'Cancelled'),
    )
    PAYMENT_METHOD_CHOICES = (
        ('COD', 'Cash on Delivery'),
        ('UPI', 'UPI'),
        ('CREDIT_CARD', 'Credit Card'),
        ('DEBIT_CARD', 'Debit Card'),
    )
    username = models.CharField(max_length=150, blank=True)
    email = models.EmailField(blank=True)
    shipping_address = models.ForeignKey(ShippingAddress, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    delivery_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='COD')
    coupon = models.ForeignKey('Coupon', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Order #{self.id}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
class VendorOrder(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='vendor_orders')
    seller_username = models.CharField(max_length=150)
    status = models.CharField(max_length=20, choices=Order.STATUS_CHOICES, default='Pending')
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Vendor Order for {self.seller_username} under Order #{self.order.id}"

class SellerEarnings(models.Model):
    seller_username = models.CharField(max_length=150)
    vendor_order = models.OneToOneField(VendorOrder, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=[('Pending', 'Pending'), ('Paid', 'Paid')], default='Pending')
    paid_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Earnings for {self.seller_username} - Order #{self.vendor_order.order.id}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    vendor_order = models.ForeignKey(VendorOrder, on_delete=models.SET_NULL, null=True, blank=True, related_name='vendor_items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    selected_size = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        size_info = f" ({self.selected_size})" if self.selected_size else ""
        return f"{self.quantity} x {self.product.name if self.product else 'Deleted Product'}{size_info}"

class OrderTracking(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='tracking_history')
    status = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.order.id} - {self.status}"

class DeliveryArea(models.Model):
    pincode = models.CharField(max_length=10, unique=True)
    is_active = models.BooleanField(default=True)
    estimated_days = models.PositiveIntegerField(default=3)

    def __str__(self):
        return f"{self.pincode} ({'Active' if self.is_active else 'Inactive'})"

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    order_item = models.OneToOneField(OrderItem, on_delete=models.CASCADE, related_name='review', null=True, blank=True)
    username = models.CharField(max_length=150, blank=True)
    email = models.EmailField(blank=True)
    rating = models.PositiveIntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified_purchase = models.BooleanField(default=False)

    def __str__(self):
        return f"Review for {self.product.name} by {self.username}"

class Wishlist(models.Model):
    username = models.CharField(max_length=150, unique=True, null=True)
    email = models.EmailField(blank=True, null=True)
    products = models.ManyToManyField(Product, related_name='wishlisted_by')

    def __str__(self):
        return f"Wishlist of {self.username}"

@receiver(post_save, sender=User)
def create_wishlist(sender, instance, created, **kwargs):
    if created:
        Wishlist.objects.get_or_create(
            username=instance.username,
            defaults={'email': instance.email}
        )
