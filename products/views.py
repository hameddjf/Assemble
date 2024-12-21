from django.views.generic import ListView, DetailView
from django.db.models import Count, Min, Max, Q, F
from django.db.models.functions import Abs
from django.contrib.contenttypes.models import ContentType
from django.db.models import Prefetch

from rating.models import Rating
from comments.models import Comment 

from .models import Products
# Create your views here.


class ProductsListView(ListView):
    model = Products
    template_name = 'shop.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        queryset = super().get_queryset().filter(is_active=True)

        # فیلتر بر اساس قیمت
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')

        # اضافه کردن جستجو
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(brand__title__icontains=search_query) |  # جستجو بر اساس برند
                Q(category__name__icontains=search_query) |  # جستجو بر اساس دسته‌بندی
                Q(tags__title__icontains=search_query) |  # جستجو بر اساس تگ‌ها
                Q(parts__name__icontains=search_query)  # جستجو بر اساس قطعات
            ).distinct()  # اطمینان از عدم تکرار نتایج
            
            
        # فیلتر بر اساس دسته‌بندی
        category_name = self.request.GET.get('category')
        if category_name:
            queryset = queryset.filter(category__name=category_name)

        tag_name = self.request.GET.get('tag')
        if tag_name:
            queryset = queryset.filter(tags__title=tag_name)

        if min_price and max_price:
            queryset = queryset.filter(
                price__gte=min_price, price__lte=max_price)

        sort_by = self.request.GET.get('orderby', 'default')

        if sort_by == 'popularity':
            queryset = queryset.order_by('-sold_count')
        elif sort_by == 'latest':
            queryset = queryset.order_by('-create_at')
        elif sort_by == 'price_asc':
            queryset = sorted(queryset, key=lambda x: x.get_discount())
        elif sort_by == 'price_desc':
            queryset = sorted(
                queryset, key=lambda x: x.get_discount(), reverse=True)
        else:
            queryset = queryset.order_by('-create_at')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        price_range = Products.objects.filter(is_active=True).aggregate(
            min_price=Min('price'),
            max_price=Max('price')
        )

        context['min_price'] = price_range['min_price'] or 0
        context['max_price'] = price_range['max_price'] or 0

        categories = (
            Products.objects
            .filter(is_active=True)
            .values('category__name')
            .annotate(product_count=Count('id'))
            .order_by('-product_count')
            .distinct()[:4]
        )

        context['categories'] = categories

        start_index = (context['page_obj'].number - 1) * self.paginate_by + 1
        end_index = min(start_index + self.paginate_by -
                        1, context['paginator'].count)

        context['start_index'] = start_index
        context['end_index'] = end_index
        context['total_products'] = context['paginator'].count
        context['current_sorting'] = self.request.GET.get('orderby', 'default')

        context['search_query'] = self.request.GET.get('search', '')

        return context

class ProductDetailView(DetailView):
    model = Products
    template_name = 'shop-details.html'
    context_object_name = 'product'

    def get_similar_products(self, product):
        base_queryset = Products.objects.filter(
            category=product.category,
            is_active=True,
            stock__gt=0
        ).exclude(pk=product.pk)

        products_with_parts = []
        for similar_product in base_queryset:
            common_parts = set(product.parts.all()) & set(similar_product.parts.all())
            similar_parts_count = len(common_parts)
            if similar_parts_count > 0:
                products_with_parts.append((similar_product, similar_parts_count))
                

        if products_with_parts:
            products_with_parts.sort(
                key=lambda x: (
                    -x[1],  
                    abs(x[0].get_discount() - product.get_discount())  
                )
            )
            similar_products = [p[0] for p in products_with_parts]
        else:
            similar_products = list(
                base_queryset
                .annotate(
                    price_diff=Abs(F('price') - product.price)
                )
                .order_by('price_diff')
            )

        return similar_products[:4]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        average_rating = Rating.get_average_rating(self.object)
        
        rating_count = Rating.get_rating_count(self.object)
        
        full_stars = int(average_rating)
        half_star = average_rating - full_stars >= 0.5
        
        # دریافت نوع محتوا برای محصول
        content_type = ContentType.objects.get_for_model(Products)
        
        # دریافت کامنت‌های اصلی
        main_comments = Comment.objects.filter(
            content_type=content_type, 
            object_id=self.object.id,
            parent__isnull=True,  # فقط کامنت‌های اصلی
            status='approved'
        ).prefetch_related(
            Prefetch('replies', 
                    queryset=Comment.objects.filter(status='approved').order_by('created_at'),
                    to_attr='approved_replies'
            )
        ).order_by('-created_at')
        
        # اضافه کردن پاسخ‌های تودرتو به کامنت‌ها
        for comment in main_comments:
            comment.nested_replies = comment.get_nested_replies()
        
        # محاسبه تعداد کل کامنت‌ها (اصلی و پاسخ‌ها)
        total_comments_count = Comment.objects.filter(
            content_type=content_type, 
            object_id=self.object.id,
            status='approved'
        ).count()
        
        
        context.update({
            'similar_products': self.get_similar_products(self.object),
            'truncated_description': self.truncate_description(self.object.description, 15),
            'average_rating': average_rating,
            'rating_count': rating_count,
            'full_stars': full_stars,
            'has_half_star': half_star,
            
            'comments': main_comments,  
            'total_comments_count': total_comments_count,
        })

        return context

    def truncate_description(self, description, limit):
        words = description.split()
        if len(words) > limit:
            return ' '.join(words[:limit]) + '...'
        return description