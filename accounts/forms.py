import re
from email_validator import validate_email

from django import forms
from django.core.validators import validate_email 
from django.core.exceptions import ValidationError

from .models import Account

class SignUpForm(forms.ModelForm):
    email = forms.EmailField(
        label='ایمیل',
        widget=forms.EmailInput(attrs={
            'class': 'input100',
            'placeholder': 'ایمیل'
        }),
        required=True
    )
    
    password = forms.CharField(
        label='رمز عبور',
        widget=forms.PasswordInput(attrs={
            'class': 'input100',
            'placeholder': 'رمز عبور'
        }),
        min_length=8,
        required=True
    )

    class Meta:
        model = Account
        fields = ['email', 'password']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Account.objects.filter(email=email).exists():
            raise forms.ValidationError('این ایمیل قبلاً ثبت شده است.')
        return email

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if len(password) < 8:
            raise forms.ValidationError('رمز عبور باید حداقل 8 کاراکتر باشد')
        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.set_password(self.cleaned_data['password'])
        
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'input100', 
            'placeholder': 'ایمیل'
        }),
        error_messages={
            'required': 'لطفا ایمیل خود را وارد کنید',
            'invalid': 'لطفا یک ایمیل معتبر وارد کنید'
        }
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'input100', 
            'placeholder': 'رمز عبور'
        }),
        error_messages={
            'required': 'لطفا رمز عبور خود را وارد کنید'
        }
    )
    
    
class PasswordResetForm(forms.Form):
    email = forms.EmailField(
        validators=[validate_email],
        widget=forms.EmailInput(attrs={
            'class': 'input100', 
            'placeholder': 'ایمیل خود را وارد کنید'
        })
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        user = Account.objects.filter(email=email).first()
        
        if not user:
            raise forms.ValidationError('کاربری با این ایمیل یافت نشد')
        
        if not user.is_active:
            raise forms.ValidationError('حساب کاربری غیرفعال است')
        
        if not user.email_verified:
            raise forms.ValidationError('ایمیل شما هنوز تایید نشده است')
        
        return email
    
    
class PasswordResetConfirmForm(forms.Form):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'input100', 
            'placeholder': 'رمز عبور جدید'
        }),
        label='رمز عبور جدید',
        min_length=8,
        max_length=50
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'input100', 
            'placeholder': 'تایید رمز عبور'
        }),
        label='تایید رمز عبور',
        min_length=8,
        max_length=50
    )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        # اگر هر دو فیلد پر شده باشند
        if password and confirm_password:
            # بررسی تطابق رمزها
            if password != confirm_password:
                raise forms.ValidationError({
                    'confirm_password': 'رمزهای عبور با هم مطابقت ندارند.'
                })

        return cleaned_data
    

# Contact
def validate_phone_number(value):
        # حذف فاصله‌ها و علائم اضافی
        cleaned_value = re.sub(r'[\s\-()]', '', value)
        
        # بررسی شماره تلفن همراه ایران
        mobile_pattern = r'^(۰|0)?9\d{9}$'
        
        # بررسی شماره تلفن ثابت ایران
        landline_pattern = r'^(۰|0)?\d{10}$'
        
        if not (re.match(mobile_pattern, cleaned_value) or re.match(landline_pattern, cleaned_value)):
            raise ValidationError('شماره تماس معتبر نیست')
        
        return cleaned_value

class ContactForm(forms.Form):
    name = forms.CharField(
        label='نام کامل شما',
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'نام شما',
            'required': 'required'
        }),
        error_messages={
            'required': 'نام خود را وارد کنید',
            'max_length': 'نام نباید بیشتر از 100 کاراکتر باشد'
        }
    )
    
    phone = forms.CharField(
        label='شماره تماس شما',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'مثال: 09123456789',
            'required': 'required'
        }),
        validators=[validate_phone_number],
        error_messages={
            'required': 'شماره تماس خود را وارد کنید',
            'invalid': 'شماره تماس معتبر نیست'
        }
    )
    
    message = forms.CharField(
        label='پیام',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'متن پیام',
            'rows': '5',
            'required': 'required'
        }),
        max_length=1000,
        error_messages={
            'required': 'متن پیام را وارد کنید',
            'max_length': 'پیام نباید بیشتر از 1000 کاراکتر باشد'
        }
    )
    
    