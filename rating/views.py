
from django.views import View
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404

from products.models import Products 

from .models import Rating

# Create your views here.



class RatingCreateView(View):
    def post(self, request, *args, **kwargs):
        slug = kwargs.get('slug')
        product = get_object_or_404(Products, slug=slug)  # پیدا کردن محصول بر اساس اسلاگ
        content_type = ContentType.objects.get(model='products')
        score = request.POST.get('score')
        
        # ایجاد یا به‌روزرسانی امتیاز
        rating, created = Rating.objects.update_or_create(
            user=request.user,
            content_type=content_type,
            object_id=product.id,  # استفاده از شناسه محصول
            defaults={'score': score}
        )
        
        return HttpResponseRedirect(reverse('products:product_detail', args=[slug]))