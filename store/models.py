from django.db import models
from bulk.models import BulkUpload


# models.py
class ProductBulkUpload(BulkUpload):
    class Meta:
        proxy = True

    def __str__(self):
        return self.task_name
    

class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sku = models.CharField(max_length=100, unique=True)  # SKU for unique identification

    # Foreign Key to Category
    category = models.ForeignKey('Category', on_delete=models.CASCADE)

    # Optional attributes
    brand = models.CharField(max_length=100, null=True, blank=True)
    weight = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Product Image
    image_url = models.ImageField(upload_to='product_images/', null=True, blank=True)

    def __str__(self):
        return self.name

# models.py

class Category(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    parent_category = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

# Product Variants (e.g., Size, Color)
class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    attribute = models.CharField(max_length=100)  # e.g., "Color", "Size"
    value = models.CharField(max_length=100)  # e.g., "Red", "Large"
    extra_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.product.name} - {self.attribute}: {self.value}"

# Inventory Management
class Inventory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="inventory")
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True)
    stock_quantity = models.PositiveIntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product.name} - Stock: {self.stock_quantity}"

# models.py

# class ProductReview(models.Model):
#     product = models.ForeignKey(Product, related_name='reviews', on_delete=models.CASCADE)
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)])  # 1 to 5 rating scale
#     review_text = models.TextField()
#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"{self.product.name} - {self.rating} stars"

class ProductGallery(models.Model):
    product = models.ForeignKey(Product, related_name='gallery_images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/gallery/')




# models.py
from django.db import models
from django.conf import settings # Adjust based on your product app name
from bson.decimal128 import Decimal128
from decimal import Decimal

def ensure_decimal(value):
    if isinstance(value, Decimal128):
        return value.to_decimal()
    return Decimal(value)

class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s Cart"

    def total(self):
        return sum(item.subtotal() for item in self.items.all())

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cart', 'product')

    def __str__(self):
        return f"{self.product.name} (x{self.quantity})"

    def subtotal(self):
        return ensure_decimal(self.product.price) * self.quantity




# products/models.py

from django.db import models

class ManageFilters(models.Model):
    RANGE = 'range'
    BOOLEAN = 'boolean'
    SEARCH = 'search'
    ORDERING = 'ordering'
    BASIC = 'basic'
    DEFAULT = 'term' 

    FILTER_TYPE_CHOICES = [
        (RANGE, 'Range'),
        (BOOLEAN, 'Boolean'),
        (SEARCH, 'Search'),
        (ORDERING, 'Ordering'),
        (BASIC, 'Basic'),
    ]

    title = models.CharField(max_length=255)
    name = models.SlugField(max_length=255, unique=True)
    field_name = models.CharField(max_length=255)
    value = models.CharField(max_length=255, blank=True, null=True)
    start_value = models.FloatField(blank=True, null=True)
    end_value = models.FloatField(blank=True, null=True)
    type = models.CharField(max_length=50, choices=FILTER_TYPE_CHOICES, default=BASIC)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.title} ({self.type})"
