from azbankgateways.models import Bank

from django.db import models
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from django.forms import ValidationError

from accounts.models import Account
from products.models import Products

# Create your models here.
class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'در انتظار پرداخت'),
        ('successful', 'پرداخت موفق'),
        ('failed', 'پرداخت ناموفق'),
    ]
    bank_record = models.OneToOneField(Bank, on_delete=models.CASCADE, verbose_name=_("رکورد بانکی"), default=None)
    order = models.OneToOneField('Order', on_delete=models.CASCADE, related_name='payment', verbose_name='سفارش')
    
    tracking_code = models.CharField(max_length=100, unique=True, verbose_name='کد پیگیری')
    
    amount = models.PositiveIntegerField(verbose_name='مبلغ پرداختی')
    
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending', verbose_name='وضعیت پرداخت')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'پرداخت'
        verbose_name_plural = 'پرداخت‌ها'
    
    def __str__(self):
        return f"Payment for Order {self.order.order_number}"

class Address(models.Model):
    user = models.ForeignKey(
        'accounts.Account', on_delete=models.CASCADE, related_name='addresses')

    first_name = models.CharField(_("نام"), max_length=50)
    last_name = models.CharField(_("نام خانوادگی"), max_length=50)

    state = models.CharField(_("استان"), max_length=50)
    street= models.CharField(_("خیابان"), max_length=50)
    tag = models.CharField(_("پلاک"), max_length=50)
    city = models.CharField(_("شهر"), max_length=50)
    postal_code = models.CharField(
        _("کد پستی"),
        max_length=10,
        validators=[
            RegexValidator(
                regex=r'^\d{10}$',
                message=_("کد پستی باید ۱۰ رقم باشد")
            )
        ]
    )
    phone_number = models.CharField(
        _("شماره موبایل"),
        max_length=11,
        # unique=True,
        validators=[
            RegexValidator(
                regex=r'09(\d{9})$',
                message=_(
                    "شماره موبایل باید در فرمت صحیح وارد شود مثال: 09123456789")
            )
        ]
    )
    full_address = models.TextField(_("آدرس کامل"))
    description = models.TextField(blank=True, verbose_name='توضیحات')

    is_default = models.BooleanField(_("آدرس پیش‌فرض"), default=False)

    created_at = models.DateTimeField(_("تاریخ ایجاد"), auto_now_add=True)
    updated_at = models.DateTimeField(_("تاریخ بروزرسانی"), auto_now=True)

    class Meta:
        verbose_name = "آدرس"
        verbose_name_plural = "آدرس‌ها"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def to_dict(self):
        return {
            'full_name': self.get_full_name(),
            'province': self.province,
            'city': self.city,
            'postal_code': self.postal_code,
            'phone_number': self.phone_number,
            'full_address': self.full_address,
        }

    def save(self, *args, **kwargs):
        if self.is_default:
            Address.objects.filter(
                user=self.user, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_full_name()} - {self.full_address}"

# orders/models.py


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'در انتظار پرداخت'),
        ('processing', 'در حال پردازش'),
        ('shipped', 'ارسال شده'),
        ('delivered', 'تحویل داده شده'),
        ('cancelled', 'لغو شده'),
    ]
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    address = models.ForeignKey(Address, on_delete=models.PROTECT)

    order_number = models.CharField(max_length=32, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='وضعیت')
    # total_price = models.DecimalField(max_digits=10, decimal_places=0)
    tracking_code = models.CharField(_("کد رهگیری"),max_length=50,unique=True,null=True,blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'سفارش'
        verbose_name_plural = 'سفارشات'
        
    def calculate_total_discount(self):
        return sum(item.calculate_discount() for item in self.items.all())
    
    def calculate_total_price(self):
        return sum(item.total_price for item in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, related_name='items', on_delete=models.CASCADE, verbose_name='سفارش')
    product = models.ForeignKey(
        Products, on_delete=models.PROTECT, verbose_name='محصول')
    quantity = models.PositiveIntegerField(verbose_name='تعداد')
    total_price = models.PositiveIntegerField(
        verbose_name='قیمت کل',default=0 ,  editable=False)

    class Meta:
        verbose_name = 'آیتم سفارش'
        verbose_name_plural = 'آیتم‌های سفارش'

    def clean(self):
        if self.quantity <= 0:
            raise ValidationError(_("تعداد باید بیشتر از صفر باشد"))

    def save(self, *args, **kwargs):
        # محاسبه قیمت با در نظر گرفتن تخفیف
        if self.product.discount and self.product.discount > 0:
            # محاسبه قیمت با تخفیف
            discounted_price = self.product.price - (self.product.price * self.product.discount / 100)
            self.total_price = int(self.quantity * discounted_price)
        else:
            # قیمت بدون تخفیف
            self.total_price = self.quantity * self.product.price
        
        super().save(*args, **kwargs)
    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    def get_total_price_product(self) -> int:
        if self.product.discount and self.product.discount > 0:
            discounted_price = self.product.price - (self.product.price * self.product.discount / 100)
            return int(self.quantity * discounted_price)
        else:
            return self.quantity * self.product.price

    def calculate_total(self):
        return sum(item.total_price for item in self.items.all())
