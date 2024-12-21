from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db.models import Avg

from accounts.models import Account
# Create your models here.


class Rating(models.Model):
    user = models.ForeignKey(Account,on_delete=models.CASCADE,related_name='ratings',verbose_name='کاربر'
    )

    # Generic Foreign Key
    content_type = models.ForeignKey(ContentType,on_delete=models.CASCADE,verbose_name='نوع محتوا')
    object_id = models.PositiveIntegerField(verbose_name='شناسه محتوا')
    content_object = GenericForeignKey('content_type', 'object_id')

    score = models.PositiveSmallIntegerField(validators=[MinValueValidator(1, 'حداقل امتیاز 1 است'),MaxValueValidator(5, 'حداکثر امتیاز 5 است')],verbose_name='امتیاز')

    created_at = models.DateTimeField(auto_now_add=True,verbose_name='تاریخ ثبت')

    updated_at = models.DateTimeField(auto_now=True,verbose_name='تاریخ بروزرسانی')

    class Meta:
        verbose_name = 'امتیاز'
        verbose_name_plural = 'امتیازات'
        unique_together = ['user', 'content_type', 'object_id']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['score']),
        ]

    def __str__(self):
        return f"{self.user} - {self.score} stars"

    @classmethod
    def get_average_rating(cls, obj):
        """محاسبه میانگین امتیازات برای یک آبجکت"""
        ct = ContentType.objects.get_for_model(obj)
        avg = cls.objects.filter(
            content_type=ct,
            object_id=obj.id
        ).aggregate(Avg('score'))['score__avg']
        return round(avg, 1) if avg else 0

    @classmethod
    def get_rating_count(cls, obj):
        """تعداد امتیازات برای یک آبجکت"""
        ct = ContentType.objects.get_for_model(obj)
        return cls.objects.filter(
            content_type=ct,
            object_id=obj.id
        ).count()

    @classmethod
    def get_rating_distribution(cls, obj):
        """توزیع امتیازات برای یک آبجکت"""
        ct = ContentType.objects.get_for_model(obj)
        distribution = {i: 0 for i in range(1, 6)}
        ratings = cls.objects.filter(
            content_type=ct,
            object_id=obj.id
        ).values('score').annotate(count=models.Count('id'))

        for rating in ratings:
            distribution[rating['score']] = rating['count']

        return distribution
