from django.shortcuts import render, get_object_or_404
from .models import Product, Category
from django.db.models import Q

def product_list(request):
    """
    Block A3 & A4: 商品列表页 + 搜索功能
    """
    query = request.GET.get('q') # 获取搜索关键词
    category_id = request.GET.get('category') # 获取分类筛选
    
    products = Product.objects.filter(is_active=True) # 只显示上架的商品

    if query:
        # Block A4: 根据名称或描述搜索
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