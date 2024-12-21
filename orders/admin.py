from django.contrib import admin
from django.utils.html import format_html
from django.contrib.humanize.templatetags.humanize import intcomma

from .models import Address, Order, OrderItem , Payment

# Register your models here.
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('tracking_code', 'amount', 'status', 'created_at', 'updated_at')
    list_filter = ('status',)
    search_fields = ('tracking_code',)
    ordering = ('-created_at',)

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['user', 'get_full_name', 'state',
                    'city', 'phone_number', 'is_default_status']
    list_filter = ['state', 'city', 'is_default', 'created_at']
    search_fields = ['user__email', 'first_name',
                     'last_name', 'phone_number', 'postal_code']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    save_on_top = True

    fieldsets = (
        ('User Informations', {
            'fields': (('user', 'is_default'), ('first_name', 'last_name'),  'phone_number')
        }),
        ('Location Informations', {
            'fields': (('state', 'city'),('street', 'tag'), 'postal_code', 'full_address'), 'classes': ('collapse',)
        }),
        ('External Informations', {
            'fields': ('description', ('created_at', 'updated_at')),
            'classes': ('collapse',)
        }),
    )

    def is_default_status(self, obj):
        if obj.is_default:
            return format_html('<span style="color: green;">✔</span>')
        return format_html('<span style="color: red;">✘</span>')
    is_default_status.short_description = 'پیش‌فرض'


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    readonly_fields = ['total_price']
    autocomplete_fields = ['product']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'user', 'status_colored',
                    'tracking_code', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['order_number', 'tracking_code', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [OrderItemInline]
    date_hierarchy = 'created_at'
    save_on_top = True

    fieldsets = (
        ('Base Informations', {
            'fields': (('user', 'order_number'), ('status'))
        }),
        ('Address Informations', {
            'fields': ('address', 'tracking_code'), 'classes': ('collapse',)
        }),
        ('Times', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def status_colored(self, obj):
        colors = {
            'pending': 'orange',
            'processing': 'blue',
            'shipped': 'purple',
            'delivered': 'green',
            'cancelled': 'red',
        }
        return format_html(
            '<span style="color: {};">{}</span>',
            colors.get(obj.status, 'black'),
            obj.get_status_display()
        )
    status_colored.short_description = 'وضعیت'

    def get_readonly_fields(self, request, obj=None):
        if obj:  # در حالت ویرایش
            return self.readonly_fields + ['order_number']
        return self.readonly_fields


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'order_link', 'product_link',
                    'quantity', 'price_display', 'total_price_display']
    list_filter = ['order__status', 'product__category']
    search_fields = [
        'order__order_number',
        'product__name',
        'order__user__email'
    ]
    autocomplete_fields = ['product', 'order']
    readonly_fields = ['total_price']
    save_on_top = True

    fieldsets = (
        ('Base Informations', {
            'fields': (
                ('order', 'product'),
                ('quantity', 'total_price'),
            )
        }),
    )

    def order_link(self, obj):
        return format_html(
            '<a href="{}">{}</a>',
            f'/admin/orders/order/{obj.order.id}/change/',
            obj.order.order_number
        )
    order_link.short_description = 'سفارش'
    order_link.admin_order_field = 'order'

    def product_link(self, obj):
        return format_html(
            '<a href="{}">{}</a>',
            f'/admin/products/products/{obj.product.id}/change/',
            obj.product.name
        )
    product_link.short_description = 'محصول'
    product_link.admin_order_field = 'product'

    def price_display(self, obj):
        return format_html('{} تومان', intcomma(obj.product.price))
    price_display.short_description = 'قیمت واحد'
    price_display.admin_order_field = 'price'

    def total_price_display(self, obj):
        return format_html(
            '<span style="color: #28a745; font-weight:  bold;">{} تومان</span>',
            obj.total_price
        )
    total_price_display.short_description = 'قیمت کل'
    total_price_display.admin_order_field = 'total_price'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('order', 'product')
