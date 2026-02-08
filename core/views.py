from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login
# from django.contrib.auth.forms import UserCreationForm  <-- 已废弃
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.db import transaction
from django.core.paginator import Paginator
# === 新增引用 (Block A9 需要) ===
from django.http import JsonResponse
import json
# ==============================

from .models import Product, Category, Cart, CartItem, Order, OrderItem
from .forms import CustomUserCreationForm
from .forms import ProductForm, OrderStatusForm, ProductImageFormSet

# ==============================
# 1. 商品浏览 (Block A & C)
# ==============================

def product_list(request):
    """
    Block A3 & A4: 商品列表页 + 搜索 + 分页 (Block A5)
    """
    query = request.GET.get('q')
    category_id = request.GET.get('category')
    
    # 1. 获取所有符合条件的商品
    products_list = Product.objects.filter(is_active=True).order_by('-created_at')

    if query:
        products_list = products_list.filter(
            Q(name__icontains=query) | 
            Q(description_html__icontains=query) |
            Q(brand__icontains=query) |
            Q(material__icontains=query) |
            Q(origin__icontains=query)
        )
    
    if category_id:
        products_list = products_list.filter(category_id=category_id)

    # 2. 分页逻辑
    paginator = Paginator(products_list, 6) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'products': page_obj,
        'categories': Category.objects.all()
    }
    return render(request, 'core/product_list.html', context)

def product_detail(request, pk):
    """
    Block A6: 商品详情页
    """
    product = get_object_or_404(Product, pk=pk, is_active=True)
    return render(request, 'core/product_detail.html', {'product': product})

# ==============================
# 2. 用户注册 (Block A1)
# ==============================

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # 注册成功后直接登录
            login(request, user)
            return redirect('core:product_list')
    else:
        form = CustomUserCreationForm()
    return render(request, 'core/register.html', {'form': form})

# ==============================
# 3. 购物车逻辑 (Block A7-A10)
# ==============================

@login_required(login_url='core:login')
def add_to_cart(request, product_id):
    """
    Block A7: 添加到购物车
    """
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, item_created = CartItem.objects.get_or_create(cart=cart, product=product)
    
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        if not item_created:
            cart_item.quantity += quantity
        else:
            cart_item.quantity = quantity
    else:
        if not item_created:
            cart_item.quantity += 1
            
    # 安全检查：库存限制
    if cart_item.quantity > product.stock_quantity:
        cart_item.quantity = product.stock_quantity
            
    cart_item.save()
    cart.save()
    
    return redirect('core:cart_detail')

@login_required(login_url='core:login')
def cart_detail(request):
    """
    Block A8: 查看购物车
    """
    cart, created = Cart.objects.get_or_create(user=request.user)
    # 必须排序，否则刷新页面时商品顺序可能会变
    cart_items = cart.cartitem_set.all().order_by('id')
    
    total_price = 0
    for item in cart_items:
        item.subtotal = item.product.price * item.quantity
        total_price += item.subtotal
        
    context = {
        'cart_items': cart_items,
        'total_price': total_price
    }
    return render(request, 'core/cart_detail.html', context)

@login_required(login_url='core:login')
def remove_from_cart(request, item_id):
    """
    Block A10: 从购物车移除商品
    """
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    return redirect('core:cart_detail')

@login_required(login_url='core:login')
def update_cart_quantity(request, item_id):
    """
    Block A9 (核心修改): AJAX 更新购物车数量
    区别于旧版：这里不返回 redirect，而是返回 JsonResponse
    """
    if request.method == 'POST':
        try:
            # 1. 解析前端发来的 JSON 数据
            data = json.loads(request.body)
            quantity = int(data.get('quantity'))
            
            cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
            
            # 2. 更新逻辑
            if quantity > 0:
                # 检查库存限制
                if quantity > cart_item.product.stock_quantity:
                     return JsonResponse({'error': 'Exceeds stock limit'}, status=400)
                
                cart_item.quantity = quantity
                cart_item.save()
            else:
                # 数量为0则删除
                cart_item.delete()

            # 3. 重新计算总价（因为页面没有刷新，我们需要把算好的新总价发给前端）
            cart = cart_item.cart
            # 重新获取 items 确保数据最新
            items = cart.cartitem_set.all()
            new_total = sum(item.quantity * item.product.price for item in items)
            
            # 计算当前这一项的小计 (如果没被删除)
            new_subtotal = 0
            if quantity > 0:
                new_subtotal = cart_item.quantity * cart_item.product.price

            # 4. 返回 JSON
            return JsonResponse({
                'success': True,
                'subtotal': new_subtotal,
                'total_price': new_total,
                'cart_count': sum(item.quantity for item in items)
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
            
    return JsonResponse({'error': 'Invalid request'}, status=400)

# ==============================
# 4. 订单系统 (Block A11-A13 & Block B)
# ==============================

@login_required(login_url='core:login')
def checkout(request):
    """
    Block A11: 结算流程
    """
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.cartitem_set.all()
    
    if not cart_items.exists():
        return redirect('core:product_list')

    total_amount = 0
    for item in cart_items:
        total_amount += item.product.price * item.quantity

    with transaction.atomic():
        address_snapshot = "用户默认收货地址"
        if request.user.addresses.exists():
            addr = request.user.addresses.first()
            address_snapshot = f"{addr.recipient_name}, {addr.address_line1}, {addr.city}"

        order = Order.objects.create(
            user=request.user,
            total_amount=total_amount,
            shipping_address_snapshot=address_snapshot,
            status=Order.Status.PENDING
        )

        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                product_name_snapshot=item.product.name,
                unit_price_snapshot=item.product.price,
                quantity=item.quantity
            )
        
        cart_items.delete()

    return redirect('core:order_detail', pk=order.id)

@login_required(login_url='core:login')
def order_list(request):
    """
    Block A12: 订单历史列表
    Block B3 (新增): 支持按 status 筛选
    """
    status_filter = request.GET.get('status')
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    # 筛选逻辑
    if status_filter:
        orders = orders.filter(status=status_filter)
        
    context = {
        'orders': orders,
        # 把所有可选的状态传给模板，用于生成筛选按钮
        'status_choices': Order.Status.choices, 
        'current_status': status_filter
    }
    return render(request, 'core/order_list.html', context)

@login_required(login_url='core:login')
def order_detail(request, pk):
    """
    Block A13: 订单详情
    """
    order = get_object_or_404(Order, pk=pk, user=request.user)
    return render(request, 'core/order_detail.html', {'order': order})

# ... (保留上面所有的代码，直接在最后追加) ...

# ==========================================
# 5. 商家后台管理 (Vendor Portal) - Block A14-A20
# ==========================================

from django.contrib.auth.decorators import user_passes_test
from .forms import ProductForm, OrderStatusForm

# 权限检查函数：只有 role 是 Admin 的人才能进
def is_admin(user):
    return user.is_authenticated and user.role == 'Admin'

@login_required
@user_passes_test(is_admin, login_url='core:product_list') # 如果不是管理员，踢回首页
def vendor_dashboard(request):
    """商家后台首页 (重定向到商品列表)"""
    return redirect('core:vendor_product_list')

# --- 商品管理 (A14-A18) ---

@login_required
@user_passes_test(is_admin)
def vendor_product_list(request):
    """
    A14 & A15: 商家商品列表 (带分页和搜索)
    """
    query = request.GET.get('q')
    
    # 1. 获取所有商品，按创建时间倒序 (最新的在前面)
    products_list = Product.objects.all().order_by('-created_at')
    
    # 2. 如果有搜索，进行过滤
    if query:
        products_list = products_list.filter(
            Q(name__icontains=query) | 
            Q(id__icontains=query) |
            Q(brand__icontains=query)
        )
    
    # 3. 分页逻辑 (每页显示 10 个)
    paginator = Paginator(products_list, 10) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # 4. 渲染模板
    return render(request, 'vendor/product_list.html', {
        'products': page_obj,  # 把分页对象传给模板
        'query': query         # 把搜索词也传回去，方便翻页时保留
    })


@login_required
@user_passes_test(is_admin)
def vendor_product_add(request):
    """
    A16 & B1: 添加新商品 + 多图上传
    """
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        # 初始化 formset (注意：添加时 instance 是 None，但这里我们先不传 instance)
        formset = ProductImageFormSet(request.POST, request.FILES)
        
        if form.is_valid() and formset.is_valid():
            product = form.save() # 先保存商品，得到 product 实例
            
            # 保存图片集
            images = formset.save(commit=False)
            for image in images:
                image.product = product # 把图片关联到刚创建的商品
                image.save()
            formset.save() # 处理多对多关系或其他逻辑
            
            return redirect('core:vendor_product_list')
    else:
        form = ProductForm()
        formset = ProductImageFormSet() # 空的图片表单集
        
    return render(request, 'vendor/product_form.html', {
        'form': form, 
        'formset': formset, # 传给模板
        'title': 'Add New Product'
    })

@login_required
@user_passes_test(is_admin)
def vendor_product_edit(request, pk):
    """
    A17 & A18 & B1: 编辑商品 + 管理图片
    """
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        # 绑定现有的 product 实例，这样 formset 知道要加载哪些图片
        formset = ProductImageFormSet(request.POST, request.FILES, instance=product)
        
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save() # 这里会自动处理新增、修改和删除
            return redirect('core:vendor_product_list')
    else:
        form = ProductForm(instance=product)
        formset = ProductImageFormSet(instance=product) # 加载已有图片
        
    return render(request, 'vendor/product_form.html', {
        'form': form, 
        'formset': formset, 
        'title': f'Edit Product #{pk}'
    })
# --- 订单管理 (A19-A20) ---

@login_required
@user_passes_test(is_admin)
def vendor_order_list(request):
    """
    A19: 商家订单列表 (显示所有人的)
    """
    orders = Order.objects.all().order_by('-created_at')
    
    # 简单的状态筛选
    status = request.GET.get('status')
    if status:
        orders = orders.filter(status=status)
        
    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'vendor/order_list.html', {
        'orders': page_obj,
        'status_choices': Order.Status.choices
    })

@login_required
@user_passes_test(is_admin)
def vendor_order_detail(request, pk):
    """
    A20: 商家订单详情 + 修改状态
    """
    order = get_object_or_404(Order, pk=pk)
    
    if request.method == 'POST':
        form = OrderStatusForm(request.POST, instance=order)
        if form.is_valid():
            form.save() # Order model 里的 save() 会自动记录历史 (B4)
            return redirect('core:vendor_order_detail', pk=pk)
    else:
        form = OrderStatusForm(instance=order)
        
    return render(request, 'vendor/order_detail.html', {'order': order, 'form': form})
# ==============================
# 6. 顾客订单操作 (Block B2)
# ==============================

@login_required(login_url='core:login')
def cancel_order(request, pk):
    """
    Block B2: 顾客取消订单
    规则: 只有 Pending 或 Hold 状态的订单可以被顾客取消。
    """
    order = get_object_or_404(Order, pk=pk, user=request.user)
    
    if request.method == 'POST':
        if order.can_cancel:
            order.status = Order.Status.CANCELLED
            order.save() # 这会自动触发 OrderStatusHistory 的记录
            # (可选) 这里可以添加恢复库存的逻辑，如果你做了库存扣减的话
        return redirect('core:order_detail', pk=pk)
    
    # 如果不是 POST 请求，直接跳回详情页
    return redirect('core:order_detail', pk=pk)
