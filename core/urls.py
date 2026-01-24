from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # 首页（商品列表）
    path('', views.product_list, name='product_list'),
    # 商品详情页（例如 /product/1/）
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
]