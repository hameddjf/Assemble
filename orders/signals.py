import logging
from azbankgateways.models import Bank

from django.db.models.signals import post_save
from django.dispatch import receiver

from carts.models import Cart

from .models import Order, Payment

@receiver(post_save, sender=Bank)
def update_payment_status(sender, instance, created, **kwargs):
    try:
        # بررسی وجود پرداخت مرتبط
        try:
            payment = Payment.objects.get(bank_record=instance)
        except Payment.DoesNotExist:
            # تلاش برای یافتن سفارش مرتبط
            try:
                order = Order.objects.get(bank_record=instance)
                payment = Payment.objects.create(
                    bank_record=instance, 
                    order=order, 
                    tracking_code=instance.tracking_code, 
                    amount=instance.amount, 
                    status='pending'
                )
            except Order.DoesNotExist:
                logging.warning(f"No order found for bank record {instance.tracking_code}")
                return

        # بررسی وضعیت پرداخت بر اساس استاتوس
        if instance.status == 'COMPLETE':
            payment.status = 'successful'
            
            # به‌روزرسانی وضعیت سفارش
            if payment.order:
                payment.order.status = 'processing'
                payment.order.save()

                # دریافت سبد خرید کاربر
                cart = Cart.objects.filter(
                    user=payment.order.user, 
                    is_paid=False
                ).first()

                # محاسبه دقیق تعداد محصولات برای هر محصول از سبد خرید
                product_quantities = {}
                if cart:
                    for cart_item in cart.items.all():
                        product = cart_item.product
                        # اگر محصول قبلاً در دیکشنری نباشد، مقدار اولیه صفر
                        if product not in product_quantities:
                            product_quantities[product] = 0
                        
                        # افزایش تعداد محصول بر اساس تعداد در سبد خرید
                        product_quantities[product] += cart_item.quantity

                # کاهش موجودی و افزایش تعداد فروش برای هر محصول
                for product, quantity in product_quantities.items():
                    # لاگ کردن اطلاعات قبل از تغییر
                    logging.info(f"Before Update - Product: {product.name}, Stock: {product.stock}, Sold Count: {product.sold_count}")
                
                    # کاهش موجودی و افزایش تعداد فروش
                    product.stock -= quantity
                    product.sold_count += quantity
                    product.save()

                    # لاگ کردن اطلاعات بعد از تغییر
                    logging.info(f"After Update - Product: {product.name}, Stock: {product.stock}, Sold Count: {product.sold_count}")

                # خالی کردن سبد خرید
                if cart:
                    cart.items.all().delete()  # حذف تمام آیتم‌ها از سبد خرید

        elif instance.status in ['FAILED', 'CANCEL_BY_USER', 'RETURN_FROM_BANK']:
            payment.status = 'failed'
        
        payment.save()

        # لاگ کردن وضعیت
        logging.info(f"Payment updated: ID {payment.id}, Status {payment.status}")

    except Exception as e:
        # چاپ اطلاعات کامل خطا
        import traceback
        traceback.print_exc()
        
        logging.error(f"Error in update_payment_status signal: {str(e)}")
        print(f"Error in update_payment_status signal: {str(e)}")