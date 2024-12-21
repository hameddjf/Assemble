from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinLengthValidator
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.text import Truncator

from accounts.models import Account
# Create your models here.


class Comment(models.Model):
    REACTION_CHOICES = [
        ('like', 'لایک'),
        ('dislike', 'دیسلایک'),
        ('none', 'بدون واکنش')
    ]

    STATUS_CHOICES = [
        ('pending', 'در انتظار تایید'),
        ('approved', 'تایید شده'),
        ('rejected', 'رد شده'),
    ]

    user = models.ForeignKey(Account,on_delete=models.CASCADE,related_name='comments',
    )

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    body = models.TextField(validators=[MinLengthValidator(2, 'متن نظر باید حداقل 2 کاراکتر باشد')])

    parent = models.ForeignKey('self',null=True,blank=True,on_delete=models.CASCADE,related_name='replies')

    status = models.CharField(max_length=10,choices=STATUS_CHOICES,default='pending')

    reactions = models.ManyToManyField(Account,through='CommentReaction',related_name='comment_reactions')

    is_edited = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('کامنت')
        verbose_name_plural = _('کامنتها')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{Truncator(self.body).chars(50)} - {self.user}"

    def save(self, *args, **kwargs):
        if self.pk:
            self.is_edited = True
        super().save(*args, **kwargs)

    def get_reactions_count(self, reaction_type):
        return self.comment_reactions.filter(reaction_type=reaction_type).count()

    @property
    def like_count(self):
        return self.get_reactions_count('like')

    @property
    def dislike_count(self):
        return self.get_reactions_count('dislike')
    
    def get_user_reaction(self, user):
        """دریافت واکنش کاربر به یک کامنت"""
        try:
            return self.comment_reactions.get(user=user).reaction_type
        except CommentReaction.DoesNotExist:
            return 'none'

    def get_replies(self):
        return self.replies.filter(status='approved')

    def get_reply_count(self):
        return self.get_replies().count()
    
    def get_nested_replies(self, max_depth=5):
        def _get_replies(comment, current_depth):
            if current_depth >= max_depth:
                return []
            
            replies = list(comment.replies.filter(status='approved').order_by('created_at'))
            nested_replies = []
            
            for reply in replies:
                reply.depth = current_depth + 1
                reply.nested_replies = _get_replies(reply, current_depth + 1)  # اینجا باید به پاسخ‌های زیرمجموعه نیز پاسخ دهد
                nested_replies.append(reply)
            
            return nested_replies
        
        return _get_replies(self, 0)


class CommentReaction(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    comment = models.ForeignKey(
        Comment, on_delete=models.CASCADE, related_name='comment_reactions')
    reaction_type = models.CharField(
        max_length=7,
        choices=Comment.REACTION_CHOICES,
        default='none'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('نظر')
        verbose_name_plural = _('نظرات')
        unique_together = ['user', 'comment']
