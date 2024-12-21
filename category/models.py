from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator

from mptt.models import MPTTModel, TreeForeignKey

# Create your models here.
class Category(MPTTModel):
    name = models.CharField(max_length=200,)
    slug = models.SlugField(max_length=200,unique=True,blank=True,allow_unicode=True,db_index=True)
    parent = TreeForeignKey('self',on_delete=models.CASCADE,null=True,blank=True,related_name='children',)
    image = models.ImageField(upload_to='media/categories/%Y/%m/',blank=True,validators=[FileExtensionValidator(['jpg', 'jpeg', 'png'])],)
    is_active = models.BooleanField(default=True,verbose_name="فعال/غیرفعال")
    created = models.DateTimeField(auto_now_add=True,verbose_name="تاریخ ایجاد")
    updated = models.DateTimeField(auto_now=True,verbose_name="تاریخ بروزرسانی")

    class Meta:
        ordering = ['name']
        verbose_name = "دسته‌بندی"
        verbose_name_plural = "دسته‌بندی‌ها"
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['created']),
        ]

    def clean(self):
        if self.parent:
            if self.parent == self:
                raise ValidationError("یک دسته‌بندی نمی‌تواند والد خودش باشد.")
            if self.parent.parent and self.parent.parent == self:
                raise ValidationError("چرخه در ساختار دسته‌بندی‌ها مجاز نیست.")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('category-detail', kwargs={'slug': self.slug})

    @property
    def has_children(self):
        return self.children.exists()

    def get_ancestors(self):
        ancestors = []
        current = self.parent
        while current:
            ancestors.append(current)
            current = current.parent
        return ancestors[::-1]


class Brand(models.Model):
    title = models.CharField(max_length=16)
    slug = models.SlugField(unique=True, default=None)
    logo = models.ImageField(upload_to='media/brands/')

    class Meta:
        verbose_name = 'برند'
        verbose_name_plural = 'برندها'

    def __str__(self):
        return self.title


class Tag(models.Model):
    title = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='عنوان تگ'
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        allow_unicode=True,
        verbose_name='اسلاگ'
    )

    class Meta:
        verbose_name = 'تگ'
        verbose_name_plural = 'تگ‌ها'
        ordering = ['title']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)
        super().save(*args, **kwargs)
