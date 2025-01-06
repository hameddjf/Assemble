from jalali_date import datetime2jalali

from django.views.generic import ListView, DetailView
from django.db.models import Count , Prefetch , Q
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import redirect
from django.urls import reverse
from django.db.models import Avg

from category.models import Category, Tag
from comments.models import Comment
from rating.models import Rating

from .models import Article

# Create your views here.

class BaseArticleView:
    def get_search_queryset(self, queryset):
        """
        جستجو در مقالات
        """
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(body__icontains=search_query) |
                Q(author__email__icontains=search_query) |
                Q(category__name__icontains=search_query) |
                Q(tags__title__icontains=search_query)
            )
        return queryset

    def get_popular_tags(self):
        """
        دریافت 6 تگ پراستفاده
        """
        return Tag.objects.annotate(
            article_count=Count('blogs')
        ).order_by('-article_count')[:6]

    def get_categories(self):
        """
        دریافت دسته‌بندی‌های مقالات با تعداد مقالات
        """
        return Category.objects.filter(blogs__isnull=False).annotate(
            articles_count=Count('blogs', filter=Q(blogs__status='published'))
        ).order_by('-articles_count').distinct()[:4]

    def get_most_viewed_today(self):
        """
        دریافت 3 مقاله پربازدید یا اخیر
        """
        today = timezone.now().date()
        most_viewed_today = Article.objects.filter(
            articlehits__created_at__date=today,
            status='published',
            published_at__lte=timezone.now()
        ).annotate(
            hits_count=Count('articlehits')
        ).order_by('-hits_count')[:3]
        
        if most_viewed_today.count() < 3:
            remaining_count = 3 - most_viewed_today.count()
            recent_articles = Article.objects.filter(
                status='published',
                published_at__lte=timezone.now()
            ).exclude(
                id__in=[article.id for article in most_viewed_today]
            ).order_by('-published_at')[:remaining_count]
            
            return list(most_viewed_today) + list(recent_articles)
        return most_viewed_today

    def process_articles_dates(self, articles):
        """
        تبدیل تاریخ میلادی به شمسی برای مقالات
        """
        for article in articles:
            article.jalali_date = datetime2jalali(article.published_at).strftime('%d %B %Y')
            
            # افزودن تعداد نظرات
            article.comments_count = Comment.objects.filter(
                content_type=ContentType.objects.get_for_model(Article),
                object_id=article.id
            ).count()
        return articles
    
    
class ArticleListView(BaseArticleView, ListView):
    model = Article
    template_name = 'blogs/blog.html'
    context_object_name = 'articles'
    paginate_by = 2
    

    def get_queryset(self):
        queryset = Article.objects.filter(status='published').order_by('-published_at')
        
        tag_name = self.request.GET.get('tag')
        if tag_name:
            queryset = queryset.filter(tags__title=tag_name)
        
        # اعمال جستجو
        queryset = self.get_search_queryset(queryset)
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # افزودن اطلاعات مشترک
        context['popular_tags'] = self.get_popular_tags()
        context['most_viewed_today'] = self.get_most_viewed_today()
        context['categories'] = self.get_categories()
        
        context['most_viewed_today'] = self.get_most_viewed_today()
        
        # اطلاعات جستجو
        context['search_query'] = self.request.GET.get('search', '')
        
        return context
    
    
class ArticleDetailView(BaseArticleView, DetailView):
    model = Article
    template_name = 'blogs/blog-details.html'
    context_object_name = 'article'
    
    def get(self, request, *args, **kwargs):
        # بررسی وجود پارامتر جستجو
        search_query = request.GET.get('search')
        if search_query:
            # ریدایرکت به لیست ویو با پارامتر جستجو
            return redirect(f"{reverse('blog:article_list')}?search={search_query}")
        
        # اگر جستجو نبود، ادامه روال عادی
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        # فقط مقالات منتشر شده را نمایش دهد
        return Article.objects.filter(status='published')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # افزودن اطلاعات مشترک
        context['popular_tags'] = self.object.tags.all()
        context['categories'] = self.get_categories()
        
        # افزودن مقالات مرتبط، بعدی و قبلی
        context['related_articles'] = self.object.related_articles
        context['next_article'] = self.object.next_article
        context['previous_article'] = self.object.previous_article
        
        context['most_viewed_today'] = self.get_most_viewed_today()
        
        # دریافت نوع محتوا برای محصول
        content_type = ContentType.objects.get_for_model(Article)
        
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
        
        # اضافه کردن کامنت‌ها و تعداد کل کامنت‌ها به کانتکست
        context['comments'] = main_comments  
        context['total_comments_count'] = total_comments_count
        
        # محاسبه امتیازدهی برای مقاله
        ratings = Rating.objects.filter(content_type=content_type, object_id=self.object.id)
        average_rating = ratings.aggregate(Avg('score'))['score__avg']
        if average_rating is None:
            average_rating = 0
        rating_count = ratings.count()
        
        # اضافه کردن امتیازدهی به کانتکست
        context['average_rating'] = average_rating
        context['rating_count'] = rating_count
        context['full_stars'] = int(average_rating)
        context['has_half_star'] = average_rating - int(average_rating) >= 0.5
        
        return context