from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import Banner, JoinUs

# Register your models here.


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    # نمایش فیلدها در لیست
    list_display = ('title', 'banner_type', 'is_active')
    list_filter = ('is_active', 'video_url')  # فیلتر بر اساس وضعیت ویدیو
    search_fields = ('title',)  # امکان جستجو بر اساس عنوان
    fieldsets = (
        (None, {
            'fields': ('title', 'subtitle', 'link', 'is_active')
        }),
        ('Media', {
            'fields': ('image', 'video_url', 'banner_type'),
            'classes': ('collapse',),  # بخش میدیایی را قابل جمع شدن می‌کند
        }),
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # اضافه کردن ویژگی برای تعیین حالت تصویر یا ویدیو
        form.base_fields['banner_type'].widget.attrs[
            'onchange'] = 'toggleMediaInput(this.value);'
        return form

    class Media:
        # اضافه کردن JavaScript برای پنل مدیریت
        js = ('admin/js/banner_admin.js',)


@admin.register(JoinUs)
class JoinUsAdmin(admin.ModelAdmin):
    list_display = ('title', 'subtitle', 'link',
                    'video', 'background_thumbnail')
    search_fields = ('title', 'subtitle')
    list_filter = ('link',)

    def background_thumbnail(self, obj):
        if obj.background:
            return mark_safe(f'<img src="{obj.background.url}" style="width: 100px; height: auto;" />')
        return "No Image"
    background_thumbnail.short_description = 'Thumbnail'

    # def get_readonly_fields(self, request, obj=None):
    #     if obj:  # edit mode
    #         return ('background',)
    #     return super().get_readonly_fields(request, obj)
