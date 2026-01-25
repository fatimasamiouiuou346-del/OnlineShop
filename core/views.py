from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login
# from django.contrib.auth.forms import UserCreationForm  <-- 这行已经被我们废弃了
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.db import transaction
from .models import Product, Category, Cart, CartItem, Order, OrderItem

# 【改动点 1】引入我们在 core/forms.py 里写的自定义表单
from .forms import CustomUserCreationForm

# ==============================
# 1. 商品浏览 (Block A & C)
# ==============================

def product_list(request):
    """
    Block A3 & A4: 商品列表页 + 搜索功能
    """
    query = request.GET.get('q')
    category_id = request.GET.get('category')
    
    products = Product.objects.filter(is_active=True)

    if query:
        products = products.filter(
            Q(name__icontains=query) | 
            Q(description_html__icontains=query)
        )
    
    if category_id:
        products = products.filter(category_id=category_id)

    context = {
        'products': products,
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
        # 【改动点 2】这里改成了 CustomUserCreationForm
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # 注册成功后直接登录
            login(request, user)
            return redirect('core:product_list')
    else:
        # 【改动点 3】这里也改成了 CustomUserCreationForm
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
            
    cart_item.save()
    cart.save()
    
    return redirect('core:cart_detail')

@login_required(login_url='core:login')
def cart_detail(request):
    """
    Block A8: 查看购物车
    """
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.cartitem_set.all()
    
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

# ==============================
# 4. 订单系统 (Block A11-A13)
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
    """Block A12: 订单历史列表"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'core/order_list.html', {'orders': orders})

@login_required(login_url='core:login')
def order_detail(request, pk):
    """Block A13: 订单详情"""
    order = get_object_or_404(Order, pk=pk, user=request.user)
    return render(request, 'core/order_detail.html', {'order': order})