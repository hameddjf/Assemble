from .models import Brand
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count

from mptt.admin import DraggableMPTTAdmin

from .models import Category, Brand
# Register your models here.


@admin.action(description='فعال کردن دسته‌بندی‌های انتخاب شده')
def make_active(self, request, queryset):
    updated = queryset.update(is_active=True)
    self.message_user(request, f'{updated} دسته‌بندی با موفقیت فعال شدند.')


@admin.action(description='غیرفعال کردن دسته‌بندی‌های انتخاب شده')
def make_inactive(self, request, queryset):
    updated = queryset.update(is_active=False)
    self.message_user(
        request, f'{updated} دسته‌بندی با موفقیت غیرفعال شدند.')


@admin.register(Category)
class CategoryAdmin(DraggableMPTTAdmin):
    mptt_indent_field = "name"
    list_display = (
        'tree_actions',
        'indented_title',
        'subcategories_count',
        'is_active',
        'created',
        # 'admin_actions'
    )
    list_display_links = ('indented_title',)
    list_filter = [
        ('is_active', admin.BooleanFieldListFilter),
        ('parent', admin.RelatedOnlyFieldListFilter),
        'created'
    ]
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['is_active']
    list_per_page = 25
    actions = ['make_active', 'make_inactive']
    date_hierarchy = 'created'
    save_on_top = True

    fieldsets = (
        ('Base Information', {
            'fields': ('parent', ('name',  'slug'),),
        }),
        ('Media and settings', {
            'fields': ('image', 'is_active'), 'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            children_count=Count('children', distinct=True)
        )

    def subcategories_count(self, obj):
        return obj.children_count
    subcategories_count.short_description = 'تعداد زیردسته‌ها'
    subcategories_count.admin_order_field = 'children_count'

    def admin_actions(self, obj):
        if hasattr(obj, 'get_absolute_url'):
            view_url = obj.get_absolute_url()
            return format_html(
                '<a href="{}" target="_blank" style="background-color: #417690; color: white; '
                'padding: 5px 10px; border-radius: 3px; text-decoration: none;">نمایش</a>',
                view_url
            )
        return ''
    admin_actions.short_description = 'عملیات'


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'logo_preview']
    list_display_links = ['title', 'slug']
    search_fields = ['title', 'slug']
    prepopulated_fields = {'slug': ('title',)}
    ordering = ['title']
    save_on_top = True

    def logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: contain;" />', obj.logo.url)
        return "بدون لوگو"
    logo_preview.short_description = 'پیش‌نمایش لوگو'

    fieldsets = (
        ('Base Information', {
            'fields': (
                'title',
                'slug',
            )
        }),
        ('Logo', {
            'fields': ('logo', 'logo_preview'), 'classes': ('collapse',)
        }),
    )

    readonly_fields = ['logo_preview']

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['title'].widget.attrs['style'] = 'width: 300px'
        form.base_fields['slug'].widget.attrs['style'] = 'width: 300px'
        return form
