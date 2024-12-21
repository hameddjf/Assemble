from jalali_date import datetime2jalali

from django import template

register = template.Library()

@register.filter
def format_price(value):
    if value is None:
        return ''

    value = str(int(value))
    parts = []
    while value:
        parts.insert(0, value[-3:])
        value = value[:-3]

    formatted_value = ','.join(parts)
    return f"{formatted_value} "
    # return f"{formatted_value} تومان"




@register.filter(name='jalali_date')
def jalali_date(value, arg=None):
    """
    تبدیل تاریخ میلادی به شمسی
    
    Usage:
    {{ order.created_at|jalali_date }}
    {{ order.created_at|jalali_date:"d F Y" }}
    """
    if not value:
        return ''
    
    try:
        # تبدیل به شمسی
        jalali_dt = datetime2jalali(value)
        
        # اگر فرمت داده شده، از همان استفاده کن
        if arg:
            return jalali_dt.strftime(arg)
        
        # فرمت پیش‌فرض
        return jalali_dt.strftime('%d %B %Y')
    except:
        return str(value)
    
@register.filter
def get_item(obj, index):
    try:
        return obj[index]
    except (IndexError, TypeError):
        return None