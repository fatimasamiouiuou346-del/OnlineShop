from .models import Cart

def cart_status(request):
    """
    这个函数会在每个页面加载时运行，
    专门负责计算购物车里有多少件商品。
    """
    count = 0
    if request.user.is_authenticated:
        # 获取用户的购物车
        cart = Cart.objects.filter(user=request.user).first()
        if cart:
            # 把每一项的数量加起来 (比如买了2个苹果，3个梨，总数是5)
            for item in cart.cartitem_set.all():
                count += item.quantity
    
    # 返回给模板，变量名叫 cart_item_count
    return {'cart_item_count': count}