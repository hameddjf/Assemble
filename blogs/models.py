from django.db import models
from django.utils.text import slugify
from django.urls import reverse

from accounts.models import Account
from category.models import Category , Tag
# Create your models here.


class IpAddress(models.Model):
    ip_address = models.GenericIPAddressField(verbose_name='آدرس آیپی')
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name='تاریخ ثبت')

    class Meta:
        verbose_name = 'آدرس آیپی'
        verbose_name_plural = 'آدرس‌های آیپی'

    def __str__(self):
        return self.ip_address



class Article(models.Model):
    STATUS_CHOICES = (
        ('draft', 'پیش‌نویس'),
        ('published', 'منتشر شده'),
    )

    title = models.CharField(max_length=64,verbose_name='عنوان مقاله')
    slug = models.SlugField(max_length=72,unique=True,allow_unicode=True, verbose_name='اسلاگ')
    author = models.ForeignKey(Account,on_delete=models.CASCADE,related_name='blogs',verbose_name='نویسنده')
    image = models.ImageField(upload_to='media/blogs/images/%Y/%m/%d/',verbose_name='تصویر شاخص')
    category = models.ForeignKey(Category,on_delete=models.CASCADE,related_name='blogs',verbose_name='دسته‌بندی')
    tags = models.ManyToManyField(Tag,related_name='blogs',blank=True,verbose_name='تگ‌ها')
    body = models.TextField(verbose_name='متن مقاله')
    status = models.CharField(max_length=10,choices=STATUS_CHOICES,default='draft',verbose_name='وضعیت')
    # read_time = models.PositiveIntegerField(
    #     default=0,
    #     verbose_name='زمان مطالعه (دقیقه)'
    # )
    created_at = models.DateTimeField(auto_now_add=True,verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True,verbose_name='تاریخ بروزرسانی')
    published_at = models.DateTimeField(null=True,blank=True,verbose_name='تاریخ انتشار')
    is_featured = models.BooleanField(default=False,verbose_name='مقاله ویژه')
    # meta_keywords = models.CharField(
    #     max_length=200,
    #     blank=True,
    #     verbose_name='متا کلمات کلیدی'
    # )

    class Meta:
        verbose_name = 'مقاله'
        verbose_name_plural = 'مقالات'
        ordering = ['-published_at', '-created_at']
        indexes = [
            models.Index(fields=['-published_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('blog:article_detail', kwargs={'slug': self.slug})

    @property
    def related_articles(self):
        """گرفتن مقالات مرتبط براساس تگ‌ها"""
        return Article.objects.filter(
            tags__in=self.tags.all()
        ).exclude(id=self.id).distinct()[:3]

    @property
    def next_article(self):
        """مقاله بعدی"""
        return Article.objects.filter(
            published_at__gt=self.published_at,
            status='published'
        ).order_by('published_at').first()

    @property
    def previous_article(self):
        """مقاله قبلی"""
        return Article.objects.filter(
            published_at__lt=self.published_at,
            status='published'
        ).order_by('-published_at').first()


class ArticleHits(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    ip_address = models.ForeignKey(IpAddress, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'مقاله پرطرفدار'
        verbose_name_plural = 'مقالات پرطرفدار'
