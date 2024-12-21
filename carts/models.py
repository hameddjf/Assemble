import uuid
import random

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.urls import reverse

from accounts.models import Account
from products.models import Products
# Create your models here.
user = get_user_model()


class Cart(models.Model):
    cart_uuid = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(
        Account, null=False, default=None, on_delete=models.PROTECT)
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name='خرین بروزرسانی')
    final_price = models.PositiveIntegerField(default=0, )
    is_paid = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("سبدخرید")
        verbose_name_plural = _("سبدهای خرید")

    def __str__(self):
        # return f"Cart {self.cart_uuid} - {self.user.get_full_name()}"
        return f"Cart {self.cart_uuid} "

    def get_absolute_url(self):
        return reverse("cart", kwargs={"pk": self.pk})

    def save(self, *args, **kwargs):
        if not self.cart_uuid:
            self.cart_uuid = f"cart-{timezone.now().strftime('%Y%m%d')
                                     }-{random.randint(0, 9999)}"
        super().save(*args, **kwargs)


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items',
                             on_delete=models.CASCADE)
    product = models.ForeignKey(
        Products, related_name="cart_products", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1, )
    total_price_in_product = models.PositiveIntegerField(default=0,)
    created = models.DateTimeField(
        auto_now_add=True,  null=False)

    class Meta:
        verbose_name = _("ایتم سبدخرید")
        verbose_name_plural = _("ایتم های سبدخرید")
        indexes = [
            models.Index(fields=['cart', 'created']),
            models.Index(fields=['product', 'quantity'])
        ]

    def get_total_price_product(self) -> int:
        if self.product.discount and self.product.discount > 0:
            discounted_price = self.product.price - (self.product.price * self.product.discount / 100)
            return self.quantity * discounted_price
        else:
            return self.quantity * self.product.price

    def __str__(self):
        # return f"{self.cart.user.get_full_name} {self.product.name} {self.quantity}"
        return f"{self.cart.user.email} {self.product.name} {self.quantity}"

    def get_absolute_url(self):
        return reverse("_detail", kwargs={"pk": self.pk})

    def clean(self):
        super().clean()
        try:
            if self.product.stock < self.quantity:
                raise ValidationError({
            'quantity': ("product stuck must be grater than quantity.")
        })
        except ValidationError as e:
            raise ValidationError(e)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
