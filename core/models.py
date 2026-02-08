from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.html import mark_safe

# ==========================================
# 1. User Management
# ==========================================
class User(AbstractUser):
    class Role(models.TextChoices):
        CUSTOMER = 'Customer', 'Customer'
        ADMIN = 'Admin', 'Admin/Vendor'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CUSTOMER,
        verbose_name="Role"
    )

class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    recipient_name = models.CharField("Recipient Name", max_length=100)
    address_line1 = models.CharField("Address Line 1", max_length=255)
    city = models.CharField("City", max_length=100)
    zip_code = models.CharField("Zip Code", max_length=20)
    country = models.CharField("Country", max_length=100)
    is_default = models.BooleanField("Default Address", default=False)

    def __str__(self):
        return f"{self.recipient_name} - {self.city}"

# ==========================================
# 2. Product Catalog
# ==========================================
class Category(models.Model):
    name = models.CharField("Category Name", max_length=100)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')

    def __str__(self):
        return self.name

class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    name = models.CharField("Product Name", max_length=200)
    
    # Block A6 Attributes
    brand = models.CharField("Brand", max_length=100, blank=True, null=True)
    material = models.CharField("Material", max_length=100, blank=True, null=True)
    
    # === 新增: Block B1 Optional Video ===
    video = models.FileField("Product Video", upload_to='product_videos/', blank=True, null=True, help_text="Optional short video (MP4, WebM)")
    
    description_html = models.TextField("Description (HTML)", help_text="Supports HTML formatting")
    price = models.DecimalField("Price", max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField("Stock", default=0)
    is_active = models.BooleanField("Active (On Shelf)", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def admin_photo(self):
        first_image = self.images.first()
        if first_image:
            return mark_safe(f'<img src="{first_image.image.url}" width="50" height="50" style="object-fit:cover; border-radius: 4px;" />')
        return "No Image"
    admin_photo.short_description = 'Preview'

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField("Image File", upload_to='product_images/')
    is_primary = models.BooleanField("Is Primary", default=False)

    def __str__(self):
        return f"Image for {self.product.name}"

    def preview(self):
        if self.image:
            return mark_safe(f'<img src="{self.image.url}" width="100" />')
        return ""

class ProductAttribute(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='attributes')
    attribute_name = models.CharField("Attribute Name", max_length=50)
    attribute_value = models.CharField("Attribute Value", max_length=100)

# ==========================================
# 3. Shopping Cart
# ==========================================
class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    updated_at = models.DateTimeField(auto_now=True)

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

# ==========================================
# 4. Order System
# ==========================================
class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = 'Pending', 'Pending'
        SHIPPED = 'Shipped', 'Shipped'
        CANCELLED = 'Cancelled', 'Cancelled'
        HOLD = 'Hold', 'On Hold'
        REFUNDED = 'Refunded', 'Refunded'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    total_amount = models.DecimalField("Total Amount", max_digits=10, decimal_places=2)
    shipping_address_snapshot = models.TextField("Shipping Address Snapshot")
    status = models.CharField("Order Status", max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField("Order Date", auto_now_add=True)
    
    def save(self, *args, **kwargs):
        if self.pk:
            old_order = Order.objects.get(pk=self.pk)
            if old_order.status != self.status:
                OrderStatusHistory.objects.create(
                    order=self,
                    status=self.status,
                    comments=f"Status changed from {old_order.status} to {self.status}"
                )
        super().save(*args, **kwargs)

    @property
    def can_cancel(self):
        return self.status in [self.Status.PENDING, self.Status.HOLD]

    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_name_snapshot = models.CharField("Product Name Snapshot", max_length=200)
    quantity = models.PositiveIntegerField("Quantity", default=1)
    unit_price_snapshot = models.DecimalField("Unit Price Snapshot", max_digits=10, decimal_places=2)

    @property
    def subtotal(self):
        return self.unit_price_snapshot * self.quantity

class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history')
    status = models.CharField("Status", max_length=20)
    changed_at = models.DateTimeField("Changed At", auto_now_add=True)
    comments = models.TextField("Comments", blank=True, null=True)
    
    class Meta:
        ordering = ['-changed_at']
        
class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField("Rating", choices=[(i, str(i)) for i in range(1, 6)])
    comment = models.TextField("Comment", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)