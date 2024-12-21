from django.contrib import admin
from django.utils.html import format_html

from .models import Cart, CartItem
# Register your models here.


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('total_price_in_product', 'created')
    fields = ('product', 'quantity', 'total_price_in_product', 'created')

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('cart_uuid',  'final_price',
                    'is_paid', 'created_at', 'status_color')
    list_filter = ('is_paid', 'created_at')
    search_fields = ('cart_uuid', 'user__email',)
    readonly_fields = ('cart_uuid', 'created_at', 'updated_at', 'final_price')
    inlines = [CartItemInline]
    date_hierarchy = 'created_at'
    save_on_top = True

    fieldsets = (
        ('Base Information', {
            'fields': ('cart_uuid',  'is_paid')
        }),
        ('Pricing', {
            'fields': ('final_price',), 'classes': ('collapse',)
        }),
        ('default', {
            'fields': ('created_at',), 'classes': ('collapse',)
            # 'classes': ('full-width',),
        })
    )

    def user_info(self, obj):
        return format_html(
            '<div style="min-width:200px;">'
            '<strong>{}</strong><br>'
            '<small style="color:gray">{}</small>'
            '</div>',
            # obj.user.get_full_name() or obj.user.email,
            obj.user.email,
            # obj.user.phone
        )
    user_info.short_description = 'کاربر'

    def status_color(self, obj):
        if obj.is_paid:
            color = 'green'
            text = 'پرداخت شده'
        else:
            color = 'red'
            text = 'پرداخت نشده'
        return format_html(
            '<span style="color:{}; font-weight:bold">{}</span>',
            color, text
        )
    status_color.short_description = 'وضعیت'


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("product", "quantity",
                    "total_price_in_product", "created")
    list_filter = ('created', 'product')
    search_fields = ('cart__cart_uuid', 'product__name')
    readonly_fields = ('total_price_in_product', 'created')
    list_display_links = ['product', ]
    date_hierarchy = 'created'
    save_on_top = True

    # def has_add_permission(self, request):
    #     return False

    # def has_delete_permission(self, request):
    #     return False

    fieldsets = (
        ('base information', {
            'fields': ('cart', 'product')
        }),
        ('about product', {
            'fields': ('quantity', 'total_price_in_product')
        }),
        ('default', {
            'fields': ('created',), 'classes': ('collapse',)
            # 'classes': ('full-width',),
        })
    )
