from django.db import models

# Create your models here.


class Banner(models.Model):
    BANNER_TYPE_CHOICES = (
        ('image', 'تصویر'),
        ('video', 'ویدیو'),
    )

    title = models.CharField(max_length=255)
    subtitle = models.TextField(blank=True)
    image = models.ImageField(
        upload_to='media/banners/', blank=True, null=True)
    video_url = models.URLField(blank=True, null=True)
    link = models.URLField(blank=True, null=True)
    banner_type = models.CharField(
        max_length=10, choices=BANNER_TYPE_CHOICES, default='image')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class JoinUs(models.Model):
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=200)
    background = models.ImageField(
        upload_to='media/join_us/', blank=True, null=True)
    link = models.URLField(null=True, blank=True)
    video = models.URLField(null=True, blank=True)  # اختیاری برای ویدیو

    def __str__(self):
        return self.title
