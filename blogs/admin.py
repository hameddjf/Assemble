from django.contrib import admin
from django.utils import timezone

from .models import Article, Tag, IpAddress, ArticleHits
# Register your models here.


class ArticleHitsInline(admin.TabularInline):
    model = ArticleHits
    extra = 0
    readonly_fields = ('ip_address', 'created_at')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(IpAddress)
class IpAddressAdmin(admin.ModelAdmin):
    list_display = ['ip_address', 'created_at']
    search_fields = ['ip_address']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    save_on_top = True


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug']
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ['title']
    ordering = ['title']
    save_on_top = True


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'category', 'status',
                    'get_hits_count', 'is_featured', 'published_at']
    list_filter = ['status', 'created_at', 'category', 'is_featured', 'tags']
    search_fields = ['title', 'body']
    prepopulated_fields = {'slug': ('title',)}
    raw_id_fields = ['author']
    date_hierarchy = 'created_at'
    filter_horizontal = ['tags']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [ArticleHitsInline]
    date_hierarchy = 'created_at'
    save_on_top = True

    fieldsets = (
        ('Base Informations', {
            'fields': ('title', 'slug', 'author',  'body', 'image', 'category', 'tags')
        }),
        ('Published', {
            'fields': ('status', 'is_featured', 'published_at'), 'classes': ('collapse',)
        }),
        ('Times', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_hits_count(self, obj):
        return ArticleHits.objects.filter(article=obj).count()
    get_hits_count.short_description = 'تعداد بازدید'

    def save_model(self, request, obj, form, change):
        if not change:  # اگر مقاله جدید است
            obj.author = request.user
        if obj.status == 'published' and not obj.published_at:
            obj.published_at = timezone.now()
        super().save_model(request, obj, form, change)


@admin.register(ArticleHits)
class ArticleHitsAdmin(admin.ModelAdmin):
    list_display = ['article', 'ip_address', 'created_at']
    list_filter = ['created_at']
    search_fields = ['article__title', 'ip_address__ip_address']
    readonly_fields = ['article', 'ip_address', 'created_at']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
