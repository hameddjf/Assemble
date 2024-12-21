from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.urls import reverse

from category.models import Category, Brand , Tag
# Create your models here.


class Parts(models.Model):
    PARTS_CHOICES = [('RAM', _('رم')),
                     ('MOTHERBOARD', _("مادربرد")),
                     ('GRAFIC', _('گرافیک'))
                     ]
    name = models.CharField(max_length=16, choices=PARTS_CHOICES)
    value = models.CharField(max_length=16)
    brand = models.ForeignKey(
        Brand, null=False, default=None, on_delete=models.PROTECT)

    class Meta:
        verbose_name = _("قطعه کیس")
        verbose_name_plural = _("قطعات کیس")

    def __str__(self):
        return self.name


class Products(models.Model):
    name = models.CharField(max_length=32)
    slug = models.SlugField(max_length=40,unique=True, allow_unicode=True)
    description = models.TextField(max_length=248, blank=True)
    price = models.IntegerField(null=False, default=0)
    sold_count = models.PositiveIntegerField(default=0)
    stock = models.PositiveIntegerField(null=False, default=0)
    category = models.ForeignKey(
        Category, null=False, default=None, on_delete=models.PROTECT)
    brand = models.ForeignKey(
        Brand, null=False, default=None, on_delete=models.PROTECT)
    tags = models.ManyToManyField(
        Tag,  blank=True, default=None , related_name='product_tags')
    parts = models.ManyToManyField(
        Parts, blank=True, related_name='product_parts')
    discount = models.PositiveIntegerField(null=True, blank=True, default=0)
    poster = models.ImageField(
        upload_to='media/products/poster/%Y/%m/%d/', null=True, blank=True, default=None)
    is_active = models.BooleanField(default=True)
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-create_at']
        verbose_name = 'کیس'
        verbose_name_plural = 'کیسها'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['create_at'])
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)
        
    def get_absolute_url(self):
        return reverse('products:product_detail', kwargs={'slug': self.slug})
    

    def get_discount(self):
        if self.discount:
            return self.price - (self.price * self.discount / 100)
        return self.price


class ProductImages(models.Model):
    product = models.ForeignKey(
        Products, related_name='images_product', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='media/products/images/%Y/%m/%d/')

    class Meta:
        ordering = ('product__name',)
        verbose_name = 'تصاویر محصول'
        verbose_name_plural = 'تصاویر محصولات'

    def __str__(self):
        return f"{self.product.name} - {self.pk}"


class SpacialsProducts(models.Model):
    product = models.ManyToManyField(Products, related_name='spacial_products')

    class Meta:
        ordering = ('product__name',)
        verbose_name = 'کیس ویژه'
        verbose_name_plural = 'کیسهای ویژه'

    def __str__(self):
        return f"{self.product.name} - {self.pk}"
    
