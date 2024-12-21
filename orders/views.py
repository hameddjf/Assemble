import requests
import uuid
import logging
from azbankgateways import bankfactories, models as bank_models
from azbankgateways.exceptions import AZBankGatewaysException

from django.views import View
from django.shortcuts import redirect , render
from django.views.generic import FormView, ListView 
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy , reverse
from django.contrib import messages
from django.http import HttpResponse
from django.utils import timezone
from django.conf import settings

from carts.models import Cart

from .forms import OrderAddressForm, SelectAddressForm
from .models import Order, Address , OrderItem , Payment


# Create your views here.
class BaseCartContextMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            # احراز هویت کاربر
            if not hasattr(self, 'request') or not self.request.user.is_authenticated:
                context.update(self._get_empty_cart_context())
                return context

            # دریافت سبد خرید کاربر
            cart = Cart.objects.filter(
                user=self.request.user, 
                is_paid=False
            ).first()
            
            # اگر سبد خرید وجود ندارد
            if not cart:
                context.update(self._get_empty_cart_context())
                return context

            # دریافت آیتم‌های سبد خرید مرتبط با کاربر
            cart_items = cart.items.select_related('product')
            
            # محاسبه مجموع قیمت‌ها با در نظر گرفتن تخفیف
            total_price = sum(
                item.get_total_price_product() for item in cart_items
            )
            
            # محاسبه مجموع نهایی
            grand_total = total_price + 50000  # هزینه ثابت ارسال
            
            # به روز رسانی کانتکست
            context.update({
                'cart_items': cart_items,
                'total_price': total_price,
                'tax': 50000,
                'grand_total': grand_total,
                'quantity': cart_items.count()
            })

        except Exception as e:
            print(f"خطا در محاسبه اطلاعات سبد خرید: {e}")
            context.update(self._get_empty_cart_context())

        return context
    
    def _get_empty_cart_context(self):
        return {
            'cart_items': [],
            'total_price': 0,
            'tax': 50000,
            'grand_total': 50000,
            'quantity': 0
        }
    

    def create_order(self, address):
        try:
            # دریافت سبد خرید کاربر
            cart = Cart.objects.filter(
                user=self.request.user, 
                is_paid=False
            ).first()
            
            if not cart:
                messages.error(self.request, "سبد خرید شما خالی است")
                return None
            
            # حذف سفارش‌های قبلی با وضعیت pending
            Order.objects.filter(
                user=self.request.user,
                status='pending'
            ).delete()
            
            # ایجاد شماره سفارش منحصر به فرد
            order_number = f'ORD-{timezone.now().strftime("%Y%m%d")}-{uuid.uuid4().hex[:6].upper()}'
            
            # ایجاد سفارش جدید
            order = Order.objects.create(
                user=self.request.user,
                address=address,
                order_number=order_number,
                status='pending'
            )
            
            # ایجاد آیتم‌های سفارش از آیتم‌های سبد خرید
            for cart_item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    quantity=cart_item.quantity,
                    total_price=cart_item.get_total_price_product()
                )
            
            # تغییر وضعیت سبد خرید
            cart.save()
            
            return order
        
        except Exception as e:
            print(f"خطا در ایجاد سفارش: {e}")
            messages.error(self.request, "خطا در ایجاد سفارش")
            return None

    def update_existing_order(self, address):
        try:
            # دریافت سبد خرید کاربر
            cart = Cart.objects.filter(
                user=self.request.user, 
                is_paid=False
            ).first()
            
            if not cart:
                messages.error(self.request, "سبد خرید شما خالی است")
                return None
            
            # بررسی و دریافت سفارش موجود
            existing_order = Order.objects.filter(
                user=self.request.user,
                status='pending'
            ).first()
            
            if existing_order:
                # به‌روزرسانی آدرس سفارش
                existing_order.address = address
                existing_order.save()
                
                # حذف آیتم‌های قبلی سفارش
                existing_order.items.all().delete()
                
                # ایجاد آیتم‌های جدید سفارش از سبد خرید
                for cart_item in cart.items.all():
                    OrderItem.objects.create(
                        order=existing_order,
                        product=cart_item.product,
                        quantity=cart_item.quantity,
                        total_price=cart_item.get_total_price_product()
                    )
                
                return existing_order
            
            # اگر سفارشی وجود نداشت، سفارش جدید ایجاد کن
            return self.create_order(address)
        
        except Exception as e:
            print(f"خطا در به‌روزرسانی سفارش: {e}")
            messages.error(self.request, "خطا در به‌روزرسانی سفارش")
            return None
    
    
class AddressManagementView(LoginRequiredMixin, BaseCartContextMixin, FormView):
    template_name = 'payment/checkout.html'
    form_class = OrderAddressForm
    model = Address
    success_url = reverse_lazy('orders:payment_page')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # دریافت استان‌ها
        try:
            response = requests.get("https://iran-locations-api.ir/api/v1/fa/states")
            states = response.json()
            context['states'] = states
        except Exception as e:
            print(f"Error fetching states: {e}")
            context['states'] = []
        
        # دریافت شهرها براساس استان انتخاب شده
        selected_state = self.request.GET.get('state')
        if selected_state:
            try:
                response = requests.get(
                    f"https://iran-locations-api.ir/api/v1/fa/cities?state={selected_state}"
                )
                cities = response.json()
                # اطمینان از اینکه داده‌ها به درستی پردازش میشوند
                if isinstance(cities, list):
                    context['cities'] = [{'id': city['id']} for city in cities]
                else:
                    context['cities'] = []
            except Exception as e:
                print(f"Error fetching cities: {e}")
                context['cities'] = []
        else:
            context['cities'] = []
        
        return context

    def get(self, request, *args, **kwargs):
        form = self.get_form()
        return self.render_to_response(self.get_context_data(form=form))


    def post(self, request, *args, **kwargs):
        form = self.get_form()
        
        if form.is_valid():
            return self.form_valid(form)
        else:
            print("Form Errors:", form.errors)
            return self.form_invalid(form)

    def form_valid(self, form):
        print("Form is valid, attempting to save and redirect")
        try:
            address = form.save(commit=False)
            address.user = self.request.user
            
            # دریافت ایدی استان و شهر از فرم
            state_id = self.request.POST.get('state')
            city_id = self.request.POST.get('city')
            
            # واکشی نام استان
            try:
                states_response = requests.get("https://iran-locations-api.ir/api/v1/fa/states")
                states = states_response.json()
                state_name = next((state['name'] for state in states if str(state['id']) == str(state_id)), state_id)
                address.state = state_name
            except Exception as e:
                print(f"خطا در واکشی نام استان: {e}")
                address.state = state_id
            
            # واکشی نام شهر
            try:
                cities_response = requests.get(f"https://iran-locations-api.ir/api/v1/fa/cities?state_id={state_id}")
                cities = cities_response.json()
                city_name = next((city['name'] for city in cities if str(city['id']) == str(city_id)), city_id)
                address.city = city_name
            except Exception as e:
                print(f"خطا در واکشی نام شهر: {e}")
                address.city = city_id
            
            address.save()
            
            order = self.create_order(address)
            if not order:
                messages.error(self.request, "خطا در ایجاد سفارش")
                return self.form_invalid(form)
            
            # ذخیره شناسه سفارش در سشن برای استفاده بعدی
            self.request.session['current_order_id'] = order.id
            
            messages.success(self.request, "آدرس و سفارش با موفقیت ثبت شد")
            return redirect('orders:payment_page', order_id=order.id)
            
        except Exception as e:
            print(f"خطای کلی در ذخیره آدرس: {e}")
            messages.error(self.request, "خطا در ذخیره آدرس")
            return self.form_invalid(form)


    
class AddressListView(LoginRequiredMixin, BaseCartContextMixin, ListView):
    model = Address
    template_name = 'payment/checkout.html'
    context_object_name = 'existing_addresses'

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['address_form'] = SelectAddressForm(user=self.request.user)
        return context
    

    def post(self, request):
        selected_address_id = request.POST.get('address')
        
        if selected_address_id:
            request.session['selected_address_id'] = selected_address_id
            
            # دریافت آدرس انتخاب شده
            address = Address.objects.get(id=selected_address_id)
            
            # ایجاد سفارش
            order = self.create_order(address)
            
            if order:
                return redirect('orders:payment_page', order_id=order.id)  # هدایت به صفحه پرداخت
            
        context = {
            'existing_addresses': Address.objects.filter(user=request.user),
            'address_form': SelectAddressForm(user=request.user)
        }
        return render(request, 'payment/checkout.html', context)
    
# payment
class PaymentSelectionView(LoginRequiredMixin, View):
    def get(self, request, order_id):
        try:
            # دریافت سفارش
            order = Order.objects.get(id=order_id, user=request.user)
            total_amount = sum(item.total_price for item in order.items.all())
            context = {
                'order': order,
                'total_amount': total_amount,
                'banks': bank_models.BankType.choices  # لیست درگاه‌های بانکی
            }
            return render(request, 'payment/shopping-payment.html', context)
        except Order.DoesNotExist:
            return HttpResponse("سفارش یافت نشد", status=404)

    def post(self, request, order_id):
        selected_bank = request.POST.get('bank')
        try:
            # دریافت سفارش
            order = Order.objects.get(id=order_id, user=request.user)
            
            # محاسبه مبلغ کل
            total_amount = sum(item.total_price for item in order.items.all())
            
            # ایجاد پرداخت
            payment = Payment.objects.create(
                order=order,
                amount=total_amount,
                tracking_code=str(uuid.uuid4()),
                status='pending'
            )
            
            # تنظیم درگاه بانکی
            factory = bankfactories.BankFactory()
            bank = factory.create(
                selected_bank,  # بانک انتخاب شده
                callback_url=request.build_absolute_uri('/payment/verify/'),
            )
            
            # شروع تراکنش
            transaction_result = bank.pay(
                amount=total_amount,
                description=f'پرداخت برای سفارش {order.order_number}',
                extra_info={'payment_id': payment.id}
            )
            
            return redirect(transaction_result['gateway_url'])
        
        except Order.DoesNotExist:
            return HttpResponse("سفارش یافت نشد", status=404)
        

# gateaway
class GoToGateWayView(View):
    def get(self, request):
        # دریافت آخرین سفارش کاربر
        order = Order.objects.filter(user=request.user).last()
        if order:
            amount = order.calculate_total_price()
        else:
            amount = 1000000  # مقدار پیش‌فرض

        user_mobile_number = "+9809931835803"

        factory = bankfactories.BankFactory()
        
        try:
            bank = factory.auto_create()
            
            bank.set_request(request)
            # تنظیم مقدار پرداخت
            bank.set_amount(amount)
            
            bank.set_client_callback_url(reverse('orders:order_complete_page'))
            
            bank.set_mobile_number(user_mobile_number)

            # آماده‌سازی رکورد بانکی
            bank_record = bank.ready()
            
            # ذخیره رکورد بانکی در سفارش
            order.bank_record = bank_record
            order.save()

            # ایجاد رکورد پرداخت
            payment = Payment.objects.create(
                bank_record=bank_record,
                order=order,
                tracking_code=bank_record.tracking_code,
                amount=amount,
                status='pending'  # وضعیت اولیه
            )

            if settings.IS_SAFE_GET_GATEWAY_PAYMENT:
                context = bank.get_gateway()
                print(context)
                
                return render(request, "payment/redirect_to_bank.html", context=context)
            else:
                return bank.redirect_gateway()
        except AZBankGatewaysException as e:
            logging.critical(f"AZBankGatewaysException: {e}")
            return self.handle_exception(e, request)
        except Exception as e:
            logging.critical(f"General Exception: {e}")
            return self.handle_exception(e, request)

    def handle_exception(self, exception, request):
        if settings.IS_SAFE_GET_GATEWAY_PAYMENT:
            return render(request, "payment/redirect_to_bank.html", {'error': str(exception)})
        else:
            raise exception
        
class OrderCompleteView(LoginRequiredMixin, View):
    login_url = 'dashboard:processing_orders'

    def get(self, request):
        transID = request.GET.get('transID')

        try:
            payment = Payment.objects.get(bank_record__tracking_code=transID)
            order = payment.order

            if order.user != request.user:
                return redirect('dashboard:processing_orders')

            ordered_products = OrderItem.objects.filter(order_id=order.id)

            # محاسبه مجموع قیمت برای هر آیتم
            for item in ordered_products:
                item.total_price = item.product_price * item.quantity

            subtotal = sum(item.total_price for item in ordered_products)

            context = {
                'order': order,
                'ordered_products': ordered_products,
                'order_number': order.order_number,
                'transID': payment.bank_record.tracking_code,
                'payment': payment,
                'subtotal': subtotal,
                'bank_name': payment.bank_record.bank_type,
                'tracking_code': payment.bank_record.tracking_code,
                'amount': payment.bank_record.amount,
                'reference': payment.bank_record.reference_number,
                'bank_result': payment.bank_record.result,
                'callback_url': payment.bank_record.callback_url,
                'description': payment.bank_record.extra_information,
                'gateway_id': payment.bank_record.id,
                'created_at': payment.bank_record.created_at,
                'updated_at': payment.bank_record.updated_at,
            }
            return render(request, 'orders/order_complete.html', context)

        except Payment.DoesNotExist:
            logging.error(f"Payment not found for transID: {transID}")
            return redirect('dashboard:processing_orders')
        except Exception as e:
            logging.error(f"Error in OrderCompleteView: {str(e)}")
            return redirect('dashboard:processing_orders')


# class VerifyPaymentView(View):
#     def get(self, request):
#         try:
#             # دریافت شناسه سفارش
#             order_id = request.GET.get('order_id')
            
#             # دریافت سفارش
#             order = Order.objects.get(id=order_id)
            
#             # دریافت رکورد بانکی مرتبط
#             bank_record = Bank.objects.filter(order=order).first()
            
#             if not bank_record:
#                 messages.error(request, "رکورد بانکی یافت نشد")
#                 return redirect('some_error_page')

#             # بررسی وضعیت نهایی
#             if bank_record.status == 'COMPLETE':
#                 # به‌روزرسانی پرداخت
#                 payment, created = Payment.objects.get_or_create(
#                     order=order,
#                     defaults={
#                         'bank_record': bank_record,
#                         'tracking_code': bank_record.tracking_code,
#                         'amount': bank_record.amount,
#                         'status': 'successful'
#                     }
#                 )
                
#                 # به‌روزرسانی وضعیت سفارش
#                 order.status = 'processing'
#                 order.save()
                
#                 messages.success(request, "پرداخت با موفقیت انجام شد")
#                 return redirect('order_success_page')
            
#             else:
#                 # پرداخت ناموفق
#                 payment, created = Payment.objects.get_or_create(
#                     order=order,
#                     defaults={
#                         'bank_record': bank_record,
#                         'tracking_code': bank_record.tracking_code,
#                         'amount': bank_record.amount,
#                         'status': 'failed'
#                     }
#                 )
                
#                 messages.error(request, "پرداخت ناموفق بود")
#                 return redirect('payment_failed_page')

#         except Order.DoesNotExist:
#             messages.error(request, "سفارش یافت نشد")
#             return redirect('some_error_page')
        
#         except Exception as e:
#             logging.error(f"Verify payment error: {str(e)}")
#             messages.error(request, "خطا در تایید پرداخت")
#             return redirect('some_error_page')