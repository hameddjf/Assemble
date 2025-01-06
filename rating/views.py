
from django.views import View
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404

from products.models import Products 
from blogs.models import Article

from .models import Rating

# Create your views here.


class RatingCreateView(View):
    def post(self, request, *args, **kwargs):
        content_type = kwargs.get('content_type')
        object_slug = kwargs.get('object_slug')
        
        content_type_model = ContentType.objects.get(model=content_type)
        if content_type_model.model == 'products':
            obj = get_object_or_404(Products, slug=object_slug)
        elif content_type_model.model == 'article':
            obj = get_object_or_404(Article, slug=object_slug)
        else:
            return HttpResponseRedirect(reverse('home'))
        
        score = request.POST.get('score')
        
        rating, created = Rating.objects.update_or_create(
            user=request.user,
            content_type=content_type_model,
            object_id=obj.id,
            defaults={'score': score}
        )
        
        if content_type_model.model == 'products':
            return HttpResponseRedirect(reverse('products:product_detail', args=[obj.slug]))
        elif content_type_model.model == 'article':
            return HttpResponseRedirect(reverse('blog:article_detail', args=[obj.slug]))
