from .models import IpAddress


class SimpleMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.
        # در این قسمت کد ها قبل از ریسپانس اجرا میشن برای مثال چک کردن ایپی که در دیتابیس ذخیره شده یا ن
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')

        try:  # دریافت ایپی کاربر
            ip_address = IpAddress.objects.get(ip_address=ip)
        except IpAddress.DoesNotExist:
            ip_address = IpAddress(ip_address=ip)
            ip_address.save()  # ذخیره ایپی ادرس
        request.META['ip_address'] = ip_address

        response = self.get_response(request)

        # در این قسمت کد ها بعد از ریسپانس اجرا میشن برای مثال بعد چک کردن درصورتی ک ایپی ذخیره نشده بود ذخیره بشه
        # Code to be executed for each request/response after
        # the view is called.

        return response
