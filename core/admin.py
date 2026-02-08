from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Product, ProductImage, Order, Category, OrderStatusHistory

# 启用多图上传界面 (Block B1)
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    # A6: 在列表中显示 Brand
    list_display = ('id', 'name', 'brand', 'price', 'stock_quantity', 'is_active')
    search_fields = ('name', 'id', 'brand') 
    list_filter = ('category', 'brand', 'is_active')
    inlines = [ProductImageInline]
    # A6: 编辑页面包含新字段
    fieldsets = (
        (None, {
            'fields': ('category', 'name', 'description_html', 'price', 'stock_quantity', 'is_active')
        }),
        ('Advanced Attributes (Block A6)', {
            'fields': ('brand', 'material'),
        }),
    )
class OrderStatusInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ('changed_at',)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    # Block B3: 允许按状态过滤
    list_filter = ('status', 'created_at')
    list_display = ('id', 'user', 'total_amount', 'status', 'created_at')
    # 在订单详情里显示状态变更历史 (Block B4)
    inlines = [OrderStatusInline]

# 注册其他模型
# 使用 UserAdmin 来管理自定义用户，这样后台不仅能管理用户，还能保留修改密码等功能
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('role',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('role',)}),
    )
    list_display = UserAdmin.list_display + ('role',)
    list_filter = UserAdmin.list_filter + ('role',)

admin.site.register(Category)