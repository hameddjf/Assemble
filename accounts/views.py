import uuid
import traceback
import requests
import datetime
from allauth.socialaccount.models import SocialAccount

from django.core.cache import cache
from django.contrib import auth
from django.urls import reverse , reverse_lazy
from django.views import View
from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.views.generic import View
from django.contrib import messages
from django.core.mail import send_mail , EmailMessage
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.backends import ModelBackend
from django.views.generic.edit import FormView
from django.utils import timezone

from .models import Account
from .forms import SignUpForm, LoginForm , PasswordResetForm , PasswordResetConfirmForm , ContactForm

import logging
logger = logging.getLogger(__name__)
# Create your views here.
class RegisterView(View):
    template_name = 'accounts/signup.html'
    form_class = SignUpForm

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('accounts:login')
        form = self.form_class()
        return render(request, self.template_name, {
            'enable_google_login': True,
            'form': form
        })

    def post(self, request):
        form = self.form_class(request.POST)

        if form.is_valid():
            try:
                print(form.cleaned_data)
                # ایجاد کاربر جدید
                user = form.save(commit=False)
                user.is_active = False
                
                # ایجاد توکن تایید
                verification_token = str(uuid.uuid4())
                user.verification_token = verification_token
                
                user.save()

                # ارسال ایمیل تایید
                # current_site = get_current_site(request)
                # verification_url = f"http://{current_site.domain}/accounts/verify-email/{verification_token}"
                verification_url = request.build_absolute_uri(
                    reverse('accounts:verify_email', kwargs={'token': verification_token})
                )
                

                send_mail(
                    'تایید ایمیل',
                    f'برای تایید ایمیل خود روی لینک زیر کلیک کنید:\n{verification_url}',
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email]
                )

                messages.success(
                    request, 'لینک تایید به ایمیل شما ارسال شد. لطفا ایمیل خود را چک کنید.')
                return redirect('/accounts/login/?command-verification&email='+ user.email)

            except Exception as e:
                print(f"Full error: {e}")
                print(f"Error type: {type(e)}")
                logger.error(f"Registration error: {str(e)}")
                messages.error(request, f'خطا در ثبت نام: {str(e)}')
                return render(request, self.template_name, {'form': form})
        else:
            print(form.errors)
            logger.error(f"Form validation errors: {form.errors}")
            for field, errors in form.errors.items():
                messages.error(request, f"{field}: {errors}")
            return render(request, self.template_name, {'form': form})

class EmailBackend(ModelBackend):
    def authenticate(self, request, email=None, password=None, **kwargs):
        try:
            user = Account.objects.get(email=email)
        except Account.DoesNotExist:
            return None
        if user.check_password(password):
            return user
        return None
class LoginView(View):
    template_name = 'accounts/login.html'
    form_class = LoginForm

    def get(self, request):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = self.form_class(request.POST)
        
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')

            try:
                # اول کاربر رو با ایمیل پیدا می‌کنیم
                user = Account.objects.get(email=email)

                # بررسی وضعیت ایمیل و فعال بودن اکانت
                if not user.email_verified:
                    messages.error(request, 'ایمیل شما هنوز تایید نشده است.')
                    return render(request, self.template_name, {'form': form})

                if not user.is_active:
                    messages.error(request, 'اکانت شما غیرفعال شده است.')
                    return render(request, self.template_name, {'form': form})

                # احراز هویت
                authenticated_user = auth.authenticate(email=email, password=password)

                if authenticated_user is not None:
                    auth.login(request, authenticated_user)
                    url = request.META.get('HTTP_REFERER')
                    try:
                        query = requests.utils.urlparse(url).query
                        params = dict(x.split('=') for x in query.split('&'))
                        if 'next' in params:
                            nextPage = params['next']
                            return redirect(nextPage)
                    except ValueError:
                        return redirect('dashboard:address_list')

                else:
                    messages.error(request, 'رمز عبور یا ایمیل اشتباه است.')
                
            except Account.DoesNotExist:
                messages.error(request, 'کاربری با این ایمیل یافت نشد.')
        
        return render(request, self.template_name, {'form': form})

class GoogleLoginCallbackView(View):
    def get(self, request):
        if request.user.is_authenticated:
            # بررسی اینکه آیا این اولین ورود با گوگل است
            social_account = SocialAccount.objects.filter(
                user=request.user).first()
            if social_account and not request.user.is_verified:
                request.user.verify_email()  # تایید خودکار ایمیل برای کاربران گوگل
                messages.success(request, 'حساب کاربری شما با موفقیت ایجاد شد')
            return redirect('accounts:login')
        return redirect('accounts:login')


class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('accounts:login')

class VerifyEmailView(View):
    def get(self, request, token):
        try:
            # بررسی دقیق توکن
            user = Account.objects.get(
                verification_token=token, 
                is_active=False,  # فقط کاربران غیرفعال
                email_verified=False  # فقط ایمیل‌های تایید نشده
            )
            
            # محدودیت زمانی برای توکن (مثلاً 48 ساعت)
            # اینجا فرض می‌کنیم زمان ایجاد توکن در متد ثبت نام، در فیلد created_at ذخیره شده
            if user.date_joined and (timezone.now() - user.date_joined) > datetime.timedelta(hours=48):
                messages.error(request, 'لینک تایید منقضی شده است. لطفاً مجدداً ثبت نام کنید.')
                # اختیاری: حذف کاربر غیرفعال
                user.delete()
                return redirect('accounts:register')
            
            # فعال‌سازی کاربر
            user.is_active = True
            user.email_verified = True
            
            # پاک کردن توکن بعد از تایید
            user.verification_token = None
            
            # ذخیره تغییرات
            user.save()
            
            # پیغام موفقیت
            messages.success(request, 'ایمیل شما با موفقیت تایید شد. اکنون می‌توانید وارد شوید.')
            
            return redirect('accounts:login')
        
        except Account.DoesNotExist:
            # پیغام خطای دقیق‌تر
            messages.error(request, 'لینک تایید نامعتبر است یا قبلاً استفاده شده')
            return redirect('accounts:login')
        
        except Exception as e:
            # ثبت خطاهای احتمالی
            logger.error(f"Email verification error: {str(e)}")
            messages.error(request, 'خطای سیستمی رخ داده است')
            return redirect('accounts:login')

class PasswordResetView(View):
    template_name = 'accounts/resset_password.html'
    form_class = PasswordResetForm

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard:address_list')
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = self.form_class(request.POST)

        if form.is_valid():
            email = form.cleaned_data['email']

            # بررسی اکانت گوگل
            social_account = SocialAccount.objects.filter(
                extra_data__email=email).first()
            if social_account:
                messages.error(
                    request, 'برای حساب‌های گوگل امکان بازیابی رمز عبور وجود ندارد')
                return redirect('accounts:login')

            # بررسی وجود کاربر و وریفای بودن
            user = Account.objects.filter(
                email=email, 
                is_active=True,
                email_verified=True
            ).first()

            if user:
                # ایجاد توکن با محدودیت زمانی
                token = str(uuid.uuid4())
                
                # ذخیره توکن در کش با محدودیت زمانی 1 ساعت
                cache_data = {
                    'user_id': str(user.pk),  # تبدیل UUID به استرینگ
                    'date_joined': str(timezone.now().timestamp())
                }
                
                # چاپ اطلاعات برای بررسی
                print(f"Generated Reset Token: {token}")
                print(f"Cache Data: {cache_data}")
                
                cache.set(f'reset_token_{token}', cache_data, timeout=3600)  # 1 ساعت

                # ارسال ایمیل با توکن
                reset_link = request.build_absolute_uri(
                    reverse('accounts:reset_password_confirm', kwargs={'token': token})
                )
                
                # لاگ کردن لینک برای بررسی
                print(f"Reset Link: {reset_link}")

                # ارسال ایمیل
                try:
                    # ارسال ایمیل
                    send_mail(
                        'بازیابی رمز عبور',
                        f'برای بازیابی رمز عبور روی لینک زیر کلیک کنید:\n{reset_link}',
                        settings.DEFAULT_FROM_EMAIL,
                        [user.email],
                        fail_silently=False,
                    )
                except Exception as e:
                    # لاگ خطا
                    logger.error(f"خطا در ارسال ایمیل بازیابی رمز عبور: {e}")
                    messages.error(request, 'خطا در ارسال ایمیل. لطفاً بعداً تلاش کنید.')
                    return redirect('accounts:login')
                
                messages.success(request, 'لینک بازیابی رمز عبور به ایمیل شما ارسال شد.')
                return redirect('accounts:login')

            # پیغام یکسان برای امنیت
            messages.success(
                request, 'اگر این ایمیل در سیستم ثبت و تایید شده باشد، لینک بازیابی برای شما ارسال خواهد شد')
            return redirect('accounts:login')

        return render(request, self.template_name, {'form': form})
    
class PasswordResetConfirmView(View):
    template_name = 'accounts/reset_password_confirm.html'
    form_class = PasswordResetConfirmForm  # اضافه کردن form_class

    def get(self, request, token):
        token_data = cache.get(f'reset_token_{token}')
        
        if not token_data:
            messages.error(request, 'توکن نامعتبر یا منقضی شده است.')
            return redirect('accounts:login')

        try:
            # تبدیل timestamp به datetime با timezone
            created_at = timezone.make_aware(
                timezone.datetime.fromtimestamp(float(token_data['date_joined']))
            )
            # created_at = timezone.datetime.fromtimestamp(float(token_data['date_joined']))

            # مقایسه با زمان فعلی
            if timezone.now() - created_at > timezone.timedelta(hours=1):
                cache.delete(f'reset_token_{token}')
                messages.error(request, 'توکن منقضی شده است.')
                return redirect('accounts:login')

        except Exception as e:
            print(f"خطا در پردازش توکن: {e}")
            messages.error(request, 'توکن نامعتبر است.')
            return redirect('accounts:login')

        form = self.form_class()
        return render(request, self.template_name, {
            'form': form, 
            'token': token
        })

    def post(self, request, token):
        # بررسی اعتبار توکن
        token_data = cache.get(f'reset_token_{token}')
        
        if not token_data:
            messages.error(request, 'توکن نامعتبر یا منقضی شده است.')
            return redirect('accounts:login')

        try:
            # date_joined = timezone.datetime.fromtimestamp(float(token_data['date_joined']))
            date_joined = timezone.make_aware(
                timezone.datetime.fromtimestamp(float(token_data['date_joined'])))
            # بررسی زمان انقضا
            if timezone.now() - date_joined > timezone.timedelta(hours=1):
                cache.delete(f'reset_token_{token}')
                messages.error(request, 'توکن منقضی شده است.')
                return redirect('accounts:login')

        except (ValueError, TypeError, KeyError):
            messages.error(request, 'توکن نامعتبر است.')
            return redirect('accounts:login')

        form = self.form_class(request.POST)
        
        if form.is_valid():
            # بازیابی کاربر
            try:
                user = Account.objects.get(pk=token_data['user_id'])
            except Account.DoesNotExist:
                messages.error(request, 'کاربر یافت نشد.')
                return redirect('accounts:login')

            # تنظیم رمز عبور جدید
            password = form.cleaned_data['password']
            user.set_password(password)
            user.save()

            # حذف توکن از کش
            cache.delete(f'reset_token_{token}')

            messages.success(request, 'رمز عبور با موفقیت تغییر یافت.')
            return redirect('accounts:login')

        return render(request, self.template_name, {
            'form': form, 
            'token': token
        })
        

# contact
logger = logging.getLogger(__name__)

class ContactView(FormView):
    template_name = 'contact.html'
    form_class = ContactForm
    success_url = reverse_lazy('accounts:contact')

    def form_valid(self, form):
        print("================ Form Valid Method Started ================")
        
        try:
            # دریافت داده‌های فرم
            name = form.cleaned_data.get('name')
            phone = form.cleaned_data.get('phone')
            message = form.cleaned_data.get('message')
            
            print(f"Form Data - Name: {name}")
            print(f"Form Data - Email: {phone}")
            print(f"Form Data - Message Length: {len(message) if message else 0}")
            
            # بررسی اعتبار داده‌ها
            if not all([name, phone, message]):
                print("Error: Missing required fields")
                messages.error(self.request, 'لطفاً تمام فیلدها را پر کنید')
                return super().form_invalid(form)
            
            # ارسال ایمیل
            print("Attempting to send email...")
            email_obj = EmailMessage(
                subject=f'پیام جدید از {name}',
                body=f'نام: {name}\n شماره تماس : {phone}\n\nمتن پیام:\n{message}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[settings.CONTACT_EMAIL],
                reply_to=[phone]
            )
            
            # لاگ تنظیمات ایمیل
            print(f"Email From: {settings.DEFAULT_FROM_EMAIL}")
            print(f"Email To: {settings.CONTACT_EMAIL}")
            
            # ارسال ایمیل با اطلاعات کامل
            result = email_obj.send(fail_silently=False)
            print(f"Email Send Result: {result}")
            
            # پیغام موفقیت
            messages.success(self.request, 'پیام شما با موفقیت ارسال شد.')
            print("Email sent successfully")
        
        except Exception as e:
            # چاپ خطای کامل
            print("================ ERROR OCCURRED ================")
            print(f"Error Type: {type(e).__name__}")
            print(f"Error Details: {str(e)}")
            traceback.print_exc()  # چاپ ترِیس کامل خطا
            
            # لاگ خطا
            logger.error(f"Email Send Error: {str(e)}", exc_info=True)
            
            # پیغام خطا
            messages.error(self.request, f'مشکل در ارسال پیام: {str(e)}')
        
        print("================ Form Valid Method Ended ================")
        return super().form_valid(form)

    def form_invalid(self, form):
        # چاپ خطاهای فرم در صورت نامعتبر بودن
        print("================ Form INVALID ================")
        print("Form Errors:")
        for field, errors in form.errors.items():
            print(f"{field}: {errors}")
        
        return super().form_invalid(form)