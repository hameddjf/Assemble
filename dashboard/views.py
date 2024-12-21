import requests

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404

from orders.models import Order, Address
from orders.forms import OrderAddressForm

# Create your views here.

class DashboardBaseView(LoginRequiredMixin):
    def get_base_context(self, request):
        return {
            'user': request.user,
            'processing_orders_count': Order.objects.filter(
                user=request.user, 
                status__in=['processing']
            ).count(),
            'delivered_orders_count': Order.objects.filter(
                user=request.user, 
                status='delivered'
            ).count(),
            'cancelled_orders_count': Order.objects.filter(
                user=request.user, 
                status='cancelled'
            ).count()
        }
    

    
class ProcessingOrdersView(DashboardBaseView, ListView):
    template_name = 'dashboard/order-current.html'
    context_object_name = 'orders'

    def get_queryset(self):
        return Order.objects.filter(
            user=self.request.user, 
            status__in=['processing']
        ).order_by('-created_at').prefetch_related('items__product')
    
    def post(self, request, *args, **kwargs):
        if request.POST.get('action') == 'cancel':
            return self.cancel_order(request)
        return super().post(request, *args, **kwargs)

    def cancel_order(self, request):
        order_id = request.POST.get('order_id')
        try:
            order = get_object_or_404(Order, id=order_id, user=request.user)
            if order.status in ['pending', 'processing']:
                order.status = 'cancelled'
                order.save()
                messages.success(request, 'سفارش با موفقیت لغو شد.')
            else:
                messages.error(request, 'این سفارش قابل لغو نیست.')
        except Exception as e:
            messages.error(request, f'خطا در لغو سفارش: {str(e)}')
        
        return redirect('dashboard:processing_orders')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_base_context(self.request))
        return context
    

class DeliveredOrdersView(DashboardBaseView, ListView):
    template_name = 'dashboard/order-delivered.html'
    context_object_name = 'orders'

    def get_queryset(self):
        return Order.objects.filter(
            user=self.request.user, 
            status='delivered'
        ).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_base_context(self.request))
        return context
    
class CancelledOrdersView(DashboardBaseView, ListView):
    template_name = 'dashboard/order-cancelled.html'
    context_object_name = 'orders'

    def get_queryset(self):
        return Order.objects.filter(
            user=self.request.user, 
            status='cancelled'
        ).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_base_context(self.request))
        return context
    


class DashboardAddressView(DashboardBaseView, LoginRequiredMixin, ListView):
    model = Address
    template_name = 'dashboard/order-address.html'
    context_object_name = 'addresses'

    def get_queryset(self):
        return Address.objects.filter(
            user=self.request.user
        ).order_by('-is_default', '-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        base_context = self.get_base_context(self.request)
        context.update(base_context)  
        
        context['address_form'] = OrderAddressForm()
        try:
            response = requests.get("https://iran-locations-api.ir/api/v1/fa/states")
            states = response.json()
            context['states'] = states
        except Exception as e:
            print(f"Error fetching states: {e}")
            context['states'] = []
        return context

    def post(self, request, *args, **kwargs):
        if request.POST.get('action') == 'delete':
            return self.delete_address(request)
        
        form = OrderAddressForm(request.POST)
        
        if form.is_valid():
            try:
                # دریافت آی‌دی استان و شهر
                state_id = request.POST.get('state')
                city_id = request.POST.get('city')
                
                # واکشی نام استان
                states_response = requests.get("https://iran-locations-api.ir/api/v1/fa/states")
                states = states_response.json()
                state_name = next((state['name'] for state in states if str(state['id']) == str(state_id)), state_id)
                
                # واکشی نام شهر
                cities_response = requests.get(f"https://iran-locations-api.ir/api/v1/fa/cities?state_id={state_id}")
                cities = cities_response.json()
                city_name = next((city['name'] for city in cities if str(city['id']) == str(city_id)), city_id)
                
                # ذخیره آدرس
                address = form.save(commit=False)
                address.user = request.user
                address.state = state_name  # ذخیره نام استان
                address.city = city_name    # ذخیره نام شهر
                address.save()
                
                messages.success(request, "آدرس با موفقیت ذخیره شد")
                return redirect('dashboard:address_list')
            
            except Exception as e:
                print(f"خطا در ذخیره آدرس: {e}")
                messages.error(request, "خطا در ذخیره آدرس")
                return self.get(request, *args, **kwargs)
        
        else:
            messages.error(request, "خطا در اعتبارسنجی فرم")
            return self.get(request, *args, **kwargs)

    def delete_address(self, request):
        address_id = request.POST.get('address_id')
        
        try:
            address = get_object_or_404(
                Address, 
                id=address_id, 
                user=request.user
            )
            
            if address.is_default:
                messages.error(request, 'آدرس پیش‌فرض را نمی‌توانید حذف کنید.')
                return redirect('dashboard:address_list')

            if address.order_set.exists():
                messages.error(request, 'این آدرس به دلیل داشتن سفارش قابل حذف نیست.')
                return redirect('dashboard:address_list')

            address.delete()
            messages.success(request, 'آدرس با موفقیت حذف شد.')
        
        except Exception as e:
            messages.error(request, f'خطا در حذف آدرس: {str(e)}')
        
        return redirect('dashboard:address_list')