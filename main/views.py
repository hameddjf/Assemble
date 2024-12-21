from django.views.generic import ListView

from products.models import Products, SpacialsProducts
from rating.models import Rating
from category.models import Category
from blogs.models import Article

from .models import Banner, JoinUs

# Create your views here.
class SpecialProductsListView(ListView):
    template_name = 'index-2.html'
    context_object_name = 'special_products'

    def get_queryset(self):
        special_products = SpacialsProducts.objects.prefetch_related(
            'product__images_product'
        ).distinct()

        products_with_ratings = []
        for special_product in special_products:
            for product in special_product.product.all():
                avg_rating = Rating.get_average_rating(product)
                products_with_ratings.append({
                    'product': product,
                    'avg_rating': round(avg_rating, 1),
                    'main_image': product.poster.url if product.poster else None
                })

        return products_with_ratings

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        product_categories = Products.objects.values_list('category', flat=True).distinct()
        
        parent_categories = []
        
        for category_id in product_categories:
            category = Category.objects.get(id=category_id)
            
            if category.parent:
                root_category = category.get_root()
                if root_category not in parent_categories:
                    parent_categories.append(root_category)
            else:
                if category not in parent_categories:
                    parent_categories.append(category)

        context['parent_categories'] = parent_categories

        latest_articles = Article.objects.filter(
            status='published').order_by('-published_at')[:1]
        context['latest_articles'] = latest_articles

        active_banners = Banner.objects.filter(is_active=True)
        context['active_banners'] = active_banners

        join_us_entries = JoinUs.objects.all()
        context['join_us_entries'] = join_us_entries
        
        return context
    


# def vector_search(request):
#     if request.headers.get('x-requested-with') == 'XMLHttpRequest':
#         query = request.GET.get('search', '')
#         if len(query) >= 2:
#             search_vector = SearchVector('name', weight='A') + \
#                             SearchVector('description', weight='B') + \
#                             SearchVector('brand__name', weight='B') + \
#                             SearchVector('category__name', weight='C') + \
#                             SearchVector('parts__name', weight='C') + \
#                             SearchVector('tags__name', weight='C')
            
#             search_query = SearchQuery(query, config='simple')
            
#             products = Products.objects.annotate(
#                 rank=SearchRank(search_vector, search_query)
#             ).filter(
#                 rank__gte=0.1
#             ).filter(
#                 is_active=True
#             ).order_by('-rank').distinct()[:10]

#             results = []
#             for product in products:
#                 results.append({
#                     'id': product.id,
#                     'name': product.name,
#                     'slug': product.slug,
#                     'price': product.price,
#                     'description': product.description[:100],
#                     'poster_url': product.poster.url if product.poster else None,
#                     'category': product.category.name,
#                     'brand': product.brand.name,
#                 })

#             return JsonResponse({
#                 'status': 'success',
#                 'results': results
#             })

#     return JsonResponse({
#         'status': 'error',
#         'message': 'Invalid request'
#     })