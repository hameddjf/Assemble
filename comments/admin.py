from django.contrib import admin
from django.utils.html import format_html

from .models import Comment, CommentReaction
# Register your models here.


class CommentReactionInline(admin.TabularInline):
    model = CommentReaction
    extra = 0
    readonly_fields = ['user', 'reaction_type', 'created_at']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['short_body', 'user', 'status',
                    'like_count', 'dislike_count', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['body', 'user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at', 'is_edited']
    actions = ['approve_comments', 'reject_comments']
    inlines = [CommentReactionInline]
    date_hierarchy = 'created_at'
    save_on_top = True

    def short_body(self, obj):
        return format_html(f"<span title='{obj.body}'>{obj.body[:50]}...</span>")
    short_body.short_description = 'متن نظر'

    def approve_comments(self, request, queryset):
        queryset.update(status='approved')
    approve_comments.short_description = "تایید نظرات انتخاب شده"

    def reject_comments(self, request, queryset):
        queryset.update(status='rejected')
    reject_comments.short_description = "رد نظرات انتخاب شده"

    fieldsets = (
        ('Base Information', {
            'fields': ('user', 'body', 'status')
        }),
        ('External Information', {
            'fields': ('parent', 'content_type', 'object_id'),
            'classes': ('collapse',)
        }),
        ('Times', {
            'fields': ('created_at', 'updated_at', 'is_edited'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CommentReaction)
class CommentReactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'comment', 'reaction_type', 'created_at']
    list_filter = ['reaction_type', 'created_at']
    search_fields = ['user__username', 'comment__body']
    readonly_fields = ['created_at']
    save_on_top = True
    fieldsets = (
        ('Base Information', {
            'fields': ('user', 'comment', 'reaction_type')
        }),
        ('Times', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
