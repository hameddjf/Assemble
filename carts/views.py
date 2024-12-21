from django.views.generic import DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.db.models import Sum
from django.contrib import messages

from products.models import Products
from orders.models import Address

from .models import Cart, CartItem

# Create your views here.

class CartView(LoginRequiredMixin, DetailView):
    model = Cart
    template_name = 'payment/cart.html'
    context_object_name = 'cart'

    def get_object(self, queryset=None):
        # اگر سبد خرید باز کاربر وجود نداشت، ایجاد می‌کند
        cart, created = Cart.objects.get_or_create(
            user=self.request.user, 
            is_paid=False
        )
        return cart

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        cart_items = self.object.items.select_related('product')
        
        context['cart_items'] = cart_items
        
        context['total_price'] = sum(
            item.get_total_price_product() for item in cart_items
        )
        
        context['total_quantity'] = cart_items.aggregate(
            total=Sum('quantity')
        )['total'] or 0
        
        # بررسی وجود آدرس برای کاربر
        context['has_address'] = Address.objects.filter(user=self.request.user).exists()
        
        return context

class AddToCartView(LoginRequiredMixin, View):
    def post(self, request, product_id):
        product = get_object_or_404(Products, id=product_id)
        
        # گرفتن مقدار quantity از فرم
        quantity = int(request.POST.get('quantity', 1))  # مقدار پیش‌فرض 1
        
        # بررسی موجودی محصول
        if quantity > product.stock:
            # اگر تعداد درخواست شده بیشتر از موجودی است، حداکثر تعداد مجاز را تنظیم کنید
            quantity = product.stock  # حداکثر تعداد مجاز را به موجودی محصول تنظیم کنید
            messages.warning(request, f'موجودی کافی نیست. حداکثر {quantity} مورد به سبد خرید اضافه شد.')

        # گرفتن سبد خرید باز کاربر
        cart, created = Cart.objects.get_or_create(
            user=request.user, 
            is_paid=False
        )
        
        # اگر محصول از قبل در سبد خرید وجود دارد، تعداد را افزایش می‌دهد
        cart_item, item_created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )
        
        # اگر محصول از قبل وجود داشته، تعداد را افزایش می‌دهد
        if not item_created:
            # بررسی اینکه آیا تعداد جدید به موجودی محصول تجاوز نمی‌کند
            new_quantity = cart_item.quantity + quantity
            if new_quantity > product.stock:
                new_quantity = product.stock  # حداکثر تعداد مجاز را به موجودی محصول تنظیم کنید
                messages.warning(request, f'موجودی کافی نیست. حداکثر {new_quantity} مورد به سبد خرید اضافه شد.')
            cart_item.quantity = new_quantity
            cart_item.save()
        
        # محاسبه قیمت نهایی سبد خرید
        cart.final_price = sum(
            item.get_total_price_product() for item in cart.items.all()
        )
        cart.save()
        
        messages.success(request, 'محصول به سبد خرید اضافه شد.')
        return redirect('carts:cart_detail')

class RemoveFromCartView(LoginRequiredMixin, View):
    def get(self, request, cart_item_id):
        return self.remove_cart_item(request, cart_item_id)
    
    def post(self, request, cart_item_id):
        return self.remove_cart_item(request, cart_item_id)
    
    def remove_cart_item(self, request, cart_item_id):
        cart_item = get_object_or_404(
            CartItem, 
            id=cart_item_id, 
            cart__user=request.user, 
            cart__is_paid=False
        )
        
        cart = cart_item.cart
        cart_item.delete()
        
        # محاسبه مجدد قیمت نهایی
        cart.final_price = sum(
            item.get_total_price_product() for item in cart.items.all()
        )
        cart.save()
        
        messages.success(request, 'محصول از سبد خرید حذف شد.')
        return redirect('carts:cart_detail')
    
class UpdateCartItemView(LoginRequiredMixin, View):
    def post(self, request, cart_item_id):
        cart_item = get_object_or_404(
            CartItem, 
            id=cart_item_id, 
            cart__user=request.user, 
            cart__is_paid=False
        )
        
        action = request.POST.get('action')
        current_quantity = cart_item.quantity
        product = cart_item.product
        
        if action == 'increase':
            # بررسی حداکثر موجودی محصول
            if current_quantity < product.stock:
                cart_item.quantity += 1
            else:
                messages.warning(request, f'حداکثر تعداد موجود برای این محصول {product.stock} عدد است.')
        
        elif action == 'decrease':
            # کاهش تعداد تا حداقل 1
            if current_quantity > 1:
                cart_item.quantity -= 1
            else:
                # اگر تعداد 1 باشد و بخواهد کم شود، آیتم حذف شود
                cart_item.delete()
                messages.success(request, 'محصول از سبد خرید حذف شد.')
                return redirect('carts:cart_detail')
        
        cart_item.save()
        
        # محاسبه مجدد قیمت نهایی سبد خرید
        cart = cart_item.cart
        cart.final_price = sum(
            item.get_total_price_product() for item in cart.items.all()
        )
        cart.save()
        
        messages.success(request, 'تعداد محصول به‌روز شد.')
        return redirect('carts:cart_detail')