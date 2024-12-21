import uuid

from django.core.mail import send_mail
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
from django.utils import timezone
from django.db import models

# Create your models here.


class MyAccountManager(BaseUserManager):
    def _create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('آدرس ایمیل الزامی است'))

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('is_active', True)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))

        return self._create_user(email, password, **extra_fields)


class Account(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_("آدرس ایمیل"), unique=True)
    email_verified = models.BooleanField(default=False)

    # phone_number = models.CharField(
    #     _("شماره موبایل"),
    #     max_length=11,
    #     unique=True,
    #     validators=[
    #         RegexValidator(
    #             regex=r'09(\d{9})$',
    #             message=_(
    #                 "شماره موبایل باید در فرمت صحیح وارد شود مثال: 09123456789")
    #         )
    #     ]
    # )

    is_active = models.BooleanField(_("فعال"), default=True)
    is_staff = models.BooleanField(_("کارمند"), default=False)
    is_superuser = models.BooleanField(_("ادمین کل"), default=False)

    date_joined = models.DateTimeField(_("تاریخ عضویت"), default=timezone.now)
    last_login = models.DateTimeField(_("آخرین ورود"), blank=True, null=True)

    verification_token = models.CharField(
        max_length=100, null=True, blank=True)
    reset_password_token = models.CharField(
        max_length=100, null=True, blank=True)

    objects = MyAccountManager()

    USERNAME_FIELD = 'email'

    class Meta:
        verbose_name = _('حساب کاربری')
        verbose_name_plural = _('حساب‌های کاربری')

    def __str__(self):
        return self.email

    @property
    def is_verified(self):
        """بررسی تایید شدن حساب کاربری"""
        return bool(self.email_verified)

    def verify_email(self):
        self.email_verified = True
        self.save()
        
    def email_user(self, subject, message, from_email=None, **kwargs):
        send_mail(subject, message, from_email, [self.email], **kwargs)
        
