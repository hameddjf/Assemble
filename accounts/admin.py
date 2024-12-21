from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Q

import csv
from datetime import datetime

from .models import Account

# Register your models here.


admin.site.unregister(Group)


@admin.register(Account)
class AccountAdmin(UserAdmin):
    # نمایش فیلدها در لیست
    list_display = ('email', 'email_verified_status',
                    'is_active', 'is_staff', 'last_login_display')

    # فیلترها
    list_filter = ('is_active', 'is_staff', 'email_verified',
                   'date_joined', 'last_login',)

    # فیلدهای جستجو
    search_fields = ('email',)

    # ترتیب نمایش
    ordering = ('-date_joined',)
    date_hierarchy = 'date_joined'
    save_on_top = True

    # فیلدهای نمایش در صفحه ویرایش
    fieldsets = (
        ('information account', {
            'fields': ('email', 'password')
        }),
        ('status', {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'email_verified',
            ), 'classes': ('collapse',)
        }),
        ('Important dates', {
            'fields': ('last_login', 'date_joined'), 'classes': ('collapse',)
        }),
    )

    # فیلدهای نمایش در صفحه ایجاد کاربر جدید
    add_fieldsets = (
        (_('اطلاعات اصلی'), {
            'classes': ('wide',),
            'fields': (
                'email',
                'password1',
                'password2'
            ),
        }),
    )

    # اکشن‌های دسته‌جمعی
    actions = [
        'export_as_csv',
        'verify_selected_emails',
        'activate_accounts',
        'deactivate_accounts'
    ]

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'verify-email/<uuid:user_id>/',
                self.admin_site.admin_view(self.verify_user_email),
                name='verify-user-email'
            ),
        ]
        return custom_urls + urls

    def verify_user_email(self, request, user_id):
        """تایید ایمیل کاربر از طریق پنل ادمین"""
        try:
            user = Account.objects.get(id=user_id)
            user.verify_email()
            messages.success(request,
                             f'ایمیل کاربر {user.email} با موفقیت تایید شد.')
        except Account.DoesNotExist:
            messages.error(request, 'کاربر مورد نظر یافت نشد.')
        return redirect('admin:accounts_account_changelist')

    def email_verified_status(self, obj):
        """نمایش وضعیت تایید ایمیل"""
        if obj.email_verified:
            return format_html('<img src="/static/admin/img/icon-yes.svg" alt="تایید شده">')
        return format_html(
            '<a class="button" href="{}">تایید ایمیل</a>',
            f'verify-email/{obj.id}'
        )
    email_verified_status.short_description = 'وضعیت تایید ایمیل'

    def last_login_display(self, obj):
        """نمایش آخرین ورود با رنگ‌بندی"""
        if not obj.last_login:
            return '-'
        days_diff = (datetime.now() - obj.last_login.replace(tzinfo=None)).days
        if days_diff > 30:
            return format_html(
                '<span style="color: red;">{}</span>',
                obj.last_login.strftime('%Y-%m-%d %H:%M')
            )
        return obj.last_login.strftime('%Y-%m-%d %H:%M')
    last_login_display.short_description = 'آخرین ورود'

    def export_as_csv(self, request, queryset):
        """خروجی CSV از کاربران انتخاب شده"""
        meta = self.model._meta
        field_names = [field.name for field in meta.fields]

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=users.csv'
        writer = csv.writer(response)

        writer.writerow(field_names)
        for obj in queryset:
            writer.writerow([getattr(obj, field) for field in field_names])

        return response
    export_as_csv.short_description = "خروجی CSV از کاربران انتخاب شده"

    def verify_selected_emails(self, request, queryset):
        """تایید ایمیل کاربران انتخاب شده"""
        updated = queryset.update(email_verified=True)
        self.message_user(request, f'ایمیل {
                          updated} کاربر با موفقیت تایید شد.')
    verify_selected_emails.short_description = "تایید ایمیل کاربران انتخاب شده"

    def activate_accounts(self, request, queryset):
        """فعال‌سازی حساب‌های کاربری انتخاب شده"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} حساب کاربری فعال شد.')
    activate_accounts.short_description = "فعال‌سازی حساب‌های انتخاب شده"

    def deactivate_accounts(self, request, queryset):
        """غیرفعال‌سازی حساب‌های کاربری انتخاب شده"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} حساب کاربری غیرفعال شد.')
    deactivate_accounts.short_description = "غیرفعال‌سازی حساب‌های انتخاب شده"
