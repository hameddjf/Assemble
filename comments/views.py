from django.views.generic import CreateView, UpdateView, DeleteView
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404 , redirect
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from products.models import Products
from blogs.models import Article

from .models import Comment , CommentReaction
# Create your views here.


class CommentBaseView(LoginRequiredMixin):
    model = Comment
    fields = ['body', 'parent']
    
    def get_success_url(self):
        # بازگشت به صفحه محصول یا مقاله بر اساس نوع محتوا
        content_object = self.object.content_object
        if isinstance(content_object, Products):
            return reverse_lazy('products:product_detail', kwargs={'slug': content_object.slug})
        elif isinstance(content_object, Article):
            return reverse_lazy('blog:article_detail', kwargs={'slug': content_object.slug})
        return super().get_success_url()

class CommentCreateView(CommentBaseView, CreateView):
    def form_valid(self, form):
        content_type_str = self.kwargs['content_type']  # 'product' یا 'article'
        object_id = self.kwargs['object_id']  # شناسه محصول یا مقاله
        
        if content_type_str == 'product':
            product = get_object_or_404(Products, pk=object_id)
            content_type = ContentType.objects.get_for_model(Products)
            form.instance.object_id = product.id
        elif content_type_str == 'article':
            article = get_object_or_404(Article, pk=object_id)
            content_type = ContentType.objects.get_for_model(Article)
            form.instance.object_id = article.id
        else:
            return HttpResponseBadRequest("Invalid content type")

        form.instance.user = self.request.user
        form.instance.content_type = content_type
        form.instance.status = 'pending'

        # اگر پارامتر parent در درخواست وجود دارد، آن را تنظیم کنید
        parent_id = self.request.POST.get('parent_id')
        if parent_id:
            parent_comment = get_object_or_404(Comment, id=parent_id)
            form.instance.parent = parent_comment
        
        return super().form_valid(form)
    
class CommentUpdateView(CommentBaseView, UpdateView):
    def get_queryset(self):
        # فقط کاربر مالک کامنت می‌تواند آن را ویرایش کند
        return Comment.objects.filter(user=self.request.user)

class CommentDeleteView(CommentBaseView, DeleteView):
    def get_queryset(self):
        # فقط کاربر مالک کامنت می‌تواند آن را حذف کند
        return Comment.objects.filter(user=self.request.user)
class CommentReactionView(LoginRequiredMixin, View):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, comment_id, reaction_type):
        try:
            comment = get_object_or_404(Comment, id=comment_id)
            
            # بررسی اعتبار نوع واکنش
            if reaction_type not in ['like', 'dislike', 'none']:
                return JsonResponse({'status': 'error', 'message': 'واکنش نامعتبر'}, status=400)

            # بررسی واکنش قبلی کاربر
            existing_reaction = CommentReaction.objects.filter(
                user=request.user, 
                comment=comment
            ).first()

            if existing_reaction:
                # اگر واکنش قبلی با واکنش جدید یکسان باشد، آن را حذف کن
                if existing_reaction.reaction_type == reaction_type:
                    existing_reaction.delete()
                    reaction_type = 'none'
                else:
                    # در غیر این صورت، نوع واکنش را تغییر بده
                    existing_reaction.reaction_type = reaction_type
                    existing_reaction.save()
            else:
                # ایجاد واکنش جدید
                CommentReaction.objects.create(
                    user=request.user,
                    comment=comment,
                    reaction_type=reaction_type
                )

            return redirect(request.META.get('HTTP_REFERER', '/')) # Redirect to previous page

        except Exception as e:
            return JsonResponse({
                'status': 'error', 
                'message': str(e)
            }, status=500)