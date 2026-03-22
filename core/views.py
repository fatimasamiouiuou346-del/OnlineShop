from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.db.models import Q, Sum, F
from django.db.models.functions import TruncDay, TruncMonth, TruncYear
from django.utils.dateparse import parse_date
from django.contrib import messages

import datetime
import json

from .models import Product, Category, Cart, CartItem, Order, OrderItem, Review
from .forms import CustomUserCreationForm, ProductForm, OrderStatusForm, ProductImageFormSet

# ==============================
# 1. 商品浏览 (Block A & C)
# ==============================

def product_list(request):
    query = request.GET.get('q')
    category_id = request.GET.get('category')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    
    # Start with the base queryset
    products_list = Product.objects.filter(is_active=True).order_by('-created_at')

    # Apply Search
    if query:
        products_list = products_list.filter(
            Q(name__icontains=query) | 
            Q(description_html__icontains=query) |
            Q(brand__icontains=query) |
            Q(material__icontains=query) |
            Q(origin__icontains=query) 
        )
    
    # Apply Category Filter
    if category_id and category_id != "All Categories":
        products_list = products_list.filter(category_id=category_id)

    # Apply Price Filters
    if min_price:
        products_list = products_list.filter(price__gte=min_price)
    if max_price:
        products_list = products_list.filter(price__lte=max_price)

    paginator = Paginator(products_list, 6) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'products': page_obj,
        'categories': Category.objects.all(),
        # Pass values back to template to keep inputs filled
        'selected_category': category_id,
        'min_p': min_price,
        'max_p': max_price
    }
    return render(request, 'core/product_list.html', context)


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk, is_active=True)

    related_products = []
    result = []
    
    if product.brand:
        related_products += Product.objects.filter(
            brand=product.brand, 
            is_active=True
        ).exclude(pk=pk)[:3]

    if product.category:
        related_products += Product.objects.filter(
            category=product.category, 
            is_active=True
        ).exclude(pk=pk)[:3]

    if product.origin:
        related_products += Product.objects.filter(
            origin=product.origin, 
            is_active=True
        ).exclude(pk=pk)[:3]
    
    if product.material:
        related_products += Product.objects.filter(
            material=product.material, 
            is_active=True
        ).exclude(pk=pk)[:3]

    # ==============================
    # Block T: 檢查用戶是否可以評論
    # ==============================
    user_eligibility = {
        'can_review': False,
        'has_ordered': False,
    }
    
    if request.user.is_authenticated:
        # 檢查用戶是否有該產品的訂單且已出貨
        has_shipped_order = Order.objects.filter(
            user=request.user,
            status=Order.Status.SHIPPED,
            items__product=product
        ).exists()
        
        user_eligibility['has_ordered'] = has_shipped_order
        # 商品详情页不显示评论表单，所以 can_review 设为 False
        user_eligibility['can_review'] = False

    result = related_products[:3]
    
    # 获取该商品的所有评论，按创建时间倒序排序（最新的在前）
    reviews = product.reviews.all().order_by('-created_at')
    
    context = {
        'product': product,
        'related_products': result,
        'user_eligibility': user_eligibility,
        'reviews': reviews,
    }

    return render(request, 'core/product_detail.html', context)

# ==============================
# 2. 用户注册 (Block A1)
# ==============================

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
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
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    return redirect('core:cart_detail')

@login_required(login_url='core:login')
def update_cart_quantity(request, item_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            quantity = int(data.get('quantity'))
            cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
            
            if quantity > 0:
                if quantity > cart_item.product.stock_quantity:
                     return JsonResponse({'success': False, 'error': 'Exceeds stock limit'})
                
                cart_item.quantity = quantity
                cart_item.save()
            else:
                return JsonResponse({'success': False, 'error': 'Quantity must be at least 1'})

            new_subtotal = cart_item.quantity * cart_item.product.price
            cart = cart_item.cart
            new_total = sum(item.quantity * item.product.price for item in cart.cartitem_set.all())

            return JsonResponse({
                'success': True,
                'subtotal': new_subtotal,
                'total_price': new_total,
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
            
    return JsonResponse({'success': False, 'error': 'Invalid request'})

# ==============================
# 4. 订单系统 (Block A11-A13)
# ==============================

@login_required(login_url='core:login')
def checkout(request):
    """
    Block A11: 结算流程，带库存扣除逻辑
    """
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.cartitem_set.all()
    
    if not cart_items.exists():
        return redirect('core:product_list')

    total_amount = 0
    
    # [库存检查] 结算前检查库存是否充足
    for item in cart_items:
        if item.product.stock_quantity < item.quantity:
            # 可以在这里加入错误提示 flash message
            return redirect('core:cart_detail')
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
            # [扣除库存] 下单成功后实时更新库存
            item.product.stock_quantity -= item.quantity
            item.product.save(update_fields=['stock_quantity'])
        
        cart_items.delete()

    return redirect('core:order_detail', pk=order.id)

@login_required(login_url='core:login')
def order_list(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    status_choices = Order.Status.choices
    current_status = request.GET.get('status')
    
    if current_status:
        orders = orders.filter(status=current_status)
    
    return render(request, 'core/order_list.html', {
        'orders': orders,
        'status_choices': status_choices,
        'current_status': current_status
    })


@login_required(login_url='core:login')
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    return render(request, 'core/order_detail.html', {'order': order})

@login_required(login_url='core:login')
def cancel_order(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    if request.method == 'POST':
        if order.can_cancel:
            order.status = Order.Status.CANCELLED
            order.save() 
            messages.success(request, "Order cancelled successfully.")
        else:
            messages.error(request, "This order cannot be cancelled.")
        return redirect('core:order_detail', pk=pk)
    return redirect('core:order_detail', pk=pk)

# ==========================================
# 5. 商家后台管理 (Vendor Portal) - Block A14-A20
# ==========================================
def is_admin(user):
    return user.is_authenticated and user.role == 'Admin'

@login_required
@user_passes_test(is_admin, login_url='core:product_list')
def vendor_dashboard(request):
    return redirect('core:vendor_product_list')

@login_required
@user_passes_test(is_admin)
def vendor_product_list(request):
    query = request.GET.get('q')
    products_list = Product.objects.all().order_by('-created_at')
    
    if query:
        # === 核心修复 Bug 1: 清理并判断输入是否是数字 ===
        clean_query = query.replace('#', '').strip()
        
        # 组装基础文本查询条件
        q_objects = Q(name__icontains=clean_query) | \
                    Q(brand__icontains=clean_query) | \
                    Q(material__icontains=clean_query) | \
                    Q(origin__icontains=clean_query)
        
        # 只有在输入全是数字时，才进行 ID 匹配，避免 ValueError
        if clean_query.isdigit():
            q_objects |= Q(id__icontains=clean_query)
            
        products_list = products_list.filter(q_objects)
    
    paginator = Paginator(products_list, 10) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'vendor/product_list.html', {
        'products': page_obj,  
        'query': query         
    })

# 洗图逻辑：确保只有一张主图
def _handle_primary_image(product):
    images = product.images.all()
    if not images.exists():
        return
    
    primary_images = images.filter(is_primary=True)
    if primary_images.count() > 1:
        first_primary = primary_images.first()
        images.exclude(id=first_primary.id).update(is_primary=False)
    elif primary_images.count() == 0:
        first_image = images.first()
        first_image.is_primary = True
        first_image.save()

@login_required
@user_passes_test(is_admin)
def vendor_product_add(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        formset = ProductImageFormSet(request.POST, request.FILES)
        
        if form.is_valid() and formset.is_valid():
            product = form.save()
            # 必须指定 instance，否则多图不知道挂在哪个商品下
            formset.instance = product
            images = formset.save(commit=False)
            for image in images:
                image.product = product
                image.save()
            formset.save()
            
            _handle_primary_image(product)
            return redirect('core:vendor_product_list')
    else:
        form = ProductForm()
        formset = ProductImageFormSet()
        
    # 关键：一定要把 form 和 formset 传给模板，否则页面就卡在那个只有标题的空壳了！
    return render(request, 'vendor/product_form.html', {
        'form': form, 
        'formset': formset,
        'title': 'Add New Product'
    })

@login_required
@user_passes_test(is_admin)
def vendor_product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        formset = ProductImageFormSet(request.POST, request.FILES, instance=product)
        
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            _handle_primary_image(product)
            return redirect('core:vendor_product_list')
    else:
        form = ProductForm(instance=product)
        formset = ProductImageFormSet(instance=product)
        
    return render(request, 'vendor/product_form.html', {
        'form': form, 
        'formset': formset, 
        'title': f'Edit Product #{pk}'
    })

@login_required
@user_passes_test(is_admin)
def vendor_product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
    return redirect('core:vendor_product_list')

@login_required
@user_passes_test(is_admin)
def vendor_order_list(request):
    orders = Order.objects.all().order_by('-created_at')
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
    order = get_object_or_404(Order, pk=pk)
    
    if request.method == 'POST':
        form = OrderStatusForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            return redirect('core:vendor_order_detail', pk=pk)
    else:
        form = OrderStatusForm(instance=order)
        
    return render(request, 'vendor/order_detail.html', {'order': order, 'form': form})

# ==============================
# 6. 图表与分析 (Reports and Analytics)
# ==============================

@login_required(login_url='core:login')
def analytics_dashboard(request):
    """
    报告与分析：显示销量Top3及收入折线图
    """
    # 限制仅管理员或商家可以访问图表
    if request.user.role != 'Admin':
        return redirect('core:product_list')

    # ------------------
    # 1. 销量前Top3产品
    # ------------------
    # 只统计未取消且非待处理的订单 (已完成/发货等)
    valid_orders = Order.objects.exclude(status__in=[Order.Status.CANCELLED, Order.Status.REFUNDED, Order.Status.PENDING])
    
    top_products = OrderItem.objects.filter(order__in=valid_orders).values(
        'product_name_snapshot'
    ).annotate(
        total_qty=Sum('quantity'),
        total_revenue=Sum(F('quantity') * F('unit_price_snapshot'))
    ).order_by('-total_qty')[:3]

    # ------------------
    # 2. 销售额折线图
    # ------------------
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    group_by = request.GET.get('group_by', 'day') # 选项：day, month, year

    filtered_orders = valid_orders

    # 日期范围过滤
    if start_date_str:
        start_date = parse_date(start_date_str)
        if start_date:
            filtered_orders = filtered_orders.filter(created_at__date__gte=start_date)
    if end_date_str:
        end_date = parse_date(end_date_str)
        if end_date:
            filtered_orders = filtered_orders.filter(created_at__date__lte=end_date)

    # 聚合截断粒度 (年/月/日)
    if group_by == 'year':
        trunc_func = TruncYear('created_at')
    elif group_by == 'month':
        trunc_func = TruncMonth('created_at')
    else:
        trunc_func = TruncDay('created_at')

    revenue_data = filtered_orders.annotate(
        date_group=trunc_func
    ).values('date_group').annotate(
        daily_total=Sum('total_amount')
    ).order_by('date_group')

    # 准备传给 Chart.js 的数据格式
    labels = []
    totals = []
    for item in revenue_data:
        if item['date_group']:
            # 根据粒度格式化显示标签
            if group_by == 'year':
                labels.append(item['date_group'].strftime('%Y'))
            elif group_by == 'month':
                labels.append(item['date_group'].strftime('%Y-%m'))
            else:
                labels.append(item['date_group'].strftime('%Y-%m-%d'))
            totals.append(float(item['daily_total']))

    context = {
        'top_products': top_products,
        'labels': labels,
        'totals': totals,
        'start_date': start_date_str,
        'end_date': end_date_str,
        'group_by': group_by,
    }
    return render(request, 'core/analytics.html', context)


# ==============================
# 7. Block T: 訂單評論功能 (每个订单只能评论一次，同时为每个商品创建评论)
# ==============================

def can_user_review_order(user, order):
    """
    檢查用戶是否可以評論該訂單
    條件：訂單狀態為已出貨(Shipped)，且尚未評論過
    """
    if not user.is_authenticated:
        return False
    
    # 检查订单是否属于该用户
    if order.user != user:
        return False
    
    # 检查订单状态是否为已出貨
    if order.status != Order.Status.SHIPPED:
        return False
    
    # 检查是否已经评论过（检查该订单是否有评论）
    if Review.objects.filter(order=order, user=user).exists():
        return False
    
    return True


@login_required(login_url='core:login')
def add_order_review(request, order_id):
    """
    为订单添加评论，同时为订单中的每个商品创建评论记录
    """
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # 检查是否可以评论
    if not can_user_review_order(request.user, order):
        messages.error(request, "You cannot review this order. Only shipped orders can be reviewed once.")
        return redirect('core:order_detail', pk=order_id)
    
    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        
        if not rating or not comment:
            messages.error(request, "Please provide both rating and comment.")
            return redirect('core:order_detail', pk=order_id)
        
        # 为订单中的每个商品创建评论
        for item in order.items.all():
            if item.product:
                Review.objects.create(
                    order=order,
                    user=request.user,
                    product=item.product,  # 关联到商品
                    rating=int(rating),
                    comment=comment
                )
        
        messages.success(request, "Your review has been submitted successfully!")
    
    return redirect('core:order_detail', pk=order_id)


@login_required(login_url='core:login')
def edit_order_review(request, review_id):
    """
    编辑订单评论，同时更新该订单下所有商品的评论
    """
    review = get_object_or_404(Review, id=review_id, user=request.user)
    order = review.order
    
    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        
        if rating and comment:
            # 更新该订单下所有商品的评论
            Review.objects.filter(order=order, user=request.user).update(
                rating=int(rating),
                comment=comment
            )
            messages.success(request, "Your review has been updated!")
        else:
            messages.error(request, "Please provide both rating and comment.")
        
        return redirect('core:order_detail', pk=order.id)
    
    return redirect('core:order_detail', pk=order.id)


@login_required(login_url='core:login')
def delete_order_review(request, review_id):
    """
    删除订单评论，同时删除该订单下所有商品的评论
    """
    review = get_object_or_404(Review, id=review_id, user=request.user)
    order_id = review.order.id
    
    # 删除该订单下所有评论
    Review.objects.filter(order=review.order, user=request.user).delete()
    
    messages.success(request, "Your review has been deleted.")
    return redirect('core:order_detail', pk=order_id)


# ==============================
# 8. Block W: 键盘帮助页面
# ==============================

def keyboard_help(request):
    """键盘操作帮助页面"""
    return render(request, 'core/keyboard_help.html')