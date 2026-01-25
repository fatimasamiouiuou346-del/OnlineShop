from django.db import models
from django.contrib.auth.models import AbstractUser

# ==========================================
# 1. 用户管理 (Block A & Block W)
# ==========================================
class User(AbstractUser):
    """
    继承 Django 自带的 AbstractUser，自带了登录、注册、密码加密功能。
    我们只需要添加额外的角色字段。
    """
    class Role(models.TextChoices):
        CUSTOMER = 'Customer', '顾客'
        ADMIN = 'Admin', '管理员/商家'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CUSTOMER,
        verbose_name="用户角色"
    )

class Address(models.Model):
    """用户收货地址"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    recipient_name = models.CharField("收件人", max_length=100)
    address_line1 = models.CharField("详细地址", max_length=255)
    city = models.CharField("城市", max_length=100)
    zip_code = models.CharField("邮编", max_length=20)
    country = models.CharField("国家", max_length=100)
    is_default = models.BooleanField("默认地址", default=False)

    def __str__(self):
        return f"{self.recipient_name} - {self.city}"

# ==========================================
# 2. 商品目录 (Block A & Block B & Block C)
# ==========================================
class Category(models.Model):
    """商品分类，支持无限层级"""
    name = models.CharField("分类名称", max_length=100)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')

    def __str__(self):
        return self.name

class Product(models.Model):
    """商品核心信息"""
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    name = models.CharField("商品名称", max_length=200)
    # Block C1: 支持 HTML 的详细描述
    description_html = models.TextField("商品详情(HTML)", help_text="支持 HTML 格式")
    price = models.DecimalField("价格", max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField("库存", default=0)
    # Block A18: 商家可以下架商品
    is_active = models.BooleanField("是否上架", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class ProductImage(models.Model):
    """
    Block B1: 支持一个商品对应多张图片
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    # 图片会上传到 media/product_images/ 文件夹
    image = models.ImageField("图片文件", upload_to='product_images/')
    is_primary = models.BooleanField("是否主图", default=False)

    def __str__(self):
        return f"Image for {self.product.name}"

class ProductAttribute(models.Model):
    """
    Block C2: 商品动态属性（如材质、CPU型号）
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='attributes')
    attribute_name = models.CharField("属性名", max_length=50)
    attribute_value = models.CharField("属性值", max_length=100)

# ==========================================
# 3. 购物车 (Block A7-A10) -- 这里是你之前缺少的！
# ==========================================
class Cart(models.Model):
    """购物车主表"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart for {self.user.username}"

class CartItem(models.Model):
    """购物车明细"""
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

# ==========================================
# 4. 订单系统 (Block A & Block B)
# ==========================================
class Order(models.Model):
    """订单主表"""
    # Block B2: 定义至少4种状态
    class Status(models.TextChoices):
        PENDING = 'Pending', '待发货'
        SHIPPED = 'Shipped', '已发货'
        CANCELLED = 'Cancelled', '已取消'
        HOLD = 'Hold', '暂停处理'
        REFUNDED = 'Refunded', '已退款'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    total_amount = models.DecimalField("总金额", max_digits=10, decimal_places=2)
    # 3NF: 保存下单时的地址快照
    shipping_address_snapshot = models.TextField("收货地址快照")
    status = models.CharField("订单状态", max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField("下单时间", auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"

class OrderItem(models.Model):
    """订单里的具体商品"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_name_snapshot = models.CharField("商品名快照", max_length=200)
    quantity = models.PositiveIntegerField("数量", default=1)
    unit_price_snapshot = models.DecimalField("单价快照", max_digits=10, decimal_places=2)

class OrderStatusHistory(models.Model):
    """
    Block B4: 记录订单状态变更的时间
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history')
    status = models.CharField("状态", max_length=20)
    changed_at = models.DateTimeField("变更时间", auto_now_add=True)
    comments = models.TextField("备注", blank=True, null=True)