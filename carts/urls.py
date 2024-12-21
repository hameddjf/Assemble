from django.urls import path

from . import views

app_name = 'carts'

urlpatterns = [
    path('', views.CartView.as_view(), name='cart_detail'),
    path('add/<int:product_id>/', views.AddToCartView.as_view(), name='add_to_cart'),
    path('remove/<int:cart_item_id>/', views.RemoveFromCartView.as_view(), name='remove_from_cart'),
    path('update-cart-item/<int:cart_item_id>/', views.UpdateCartItemView.as_view(), name='update_cart_item'),
    
]