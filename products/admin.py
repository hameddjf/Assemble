from django.contrib import admin
from django.utils.html import format_html

from .models import Parts, Products, ProductImages, SpacialsProducts
# Register your models here.


class ProductImagesInline(admin.TabularInline):
    model = ProductImages
    extra = 1

    def image_preview(self, obj):
        return format_html('<img src="{}" width="100" height="100" />', obj.image.url) if obj.image else ''

    image_preview.short_description = 'پیش‌نمایش تصویر'
    readonly_fields = ['image_preview']


@admin.register(Parts)
class PartsAdmin(admin.ModelAdmin):
    list_display = ['name', 'value']
    list_filter = ['name']
    search_fields = ['name', 'value']
    ordering = ['name']
    save_on_top = True


@admin.register(Products)
class ProductsAdmin(admin.ModelAdmin):
    list_display = ['id','name', 'price', 'discount_price',
                    'stock', 'is_active', 'poster_preview']
    list_filter = ['is_active', 'category', 'brand', 'parts']
    search_fields = ['name', 'description']
    readonly_fields = ['sold_count', 'create_at',
                       'update_at', 'poster_preview']
    filter_horizontal = ['parts']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImagesInline]
    date_hierarchy = 'create_at'
    save_on_top = True

    fieldsets = (
        ('Base Information', {
            'fields': ('name', 'slug', 'description', 'poster', 'poster_preview')
        }),
        ('pricing & inventory', {
            'fields': ('price', 'discount', 'stock', 'sold_count'), 'classes': ('collapse',)
        }),
        ('category & brand', {
            'fields': ('category', 'brand', 'tags', 'parts'), 'classes': ('collapse',)
        }),
        ('defualts', {
            'fields': ('is_active', 'create_at', 'update_at'), 'classes': ('collapse',)
        }),
    )

    def poster_preview(self, obj):
        if obj.poster:
            return format_html('<img src="{}" width="100" height="100" />', obj.poster.url)
        return ''
    poster_preview.short_description = 'پیش‌نمایش پوستر'

    def discount_price(self, obj):
        if obj.discount:
            return f"{obj.get_discount():,} تومان ({obj.discount}%)"
        return f"{obj.price:,} تومان"
    discount_price.short_description = 'قیمت با تخفیف'


@admin.register(SpacialsProducts)
class SpacialsProductsAdmin(admin.ModelAdmin):
    filter_horizontal = ['product']
    save_on_top = True
