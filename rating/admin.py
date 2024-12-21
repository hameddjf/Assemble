from django.contrib import admin

from .models import Rating
# Register your models here.


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ['user', 'content_type', 'object_id', 'score', 'created_at']
    list_filter = ['score', 'created_at', 'content_type']
    search_fields = ['user__username',]
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    save_on_top = True

    fieldsets = (
        ('Base Informations', {
            'fields': ('user', 'score',)
        }),
        ('Content', {
            'fields': ('content_type', 'object_id'),
            'classes': ('collapse',)
        }),
        ('Times', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
