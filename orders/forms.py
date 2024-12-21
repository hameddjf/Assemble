import re

from django import forms

from .models import Address

class OrderAddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = [
            'first_name', 'last_name', 'state', 'city', 'street',
            'tag', 'postal_code', 'phone_number', 'full_address', 'description'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'street': forms.TextInput(attrs={'class': 'form-control'}),
            'tag': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'full_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
        

    def clean_postal_code(self):
        postal_code = self.cleaned_data.get('postal_code')
        if not re.match(r'^\d{10}$', postal_code):
            raise forms.ValidationError("کد پستی باید ۱۰ رقم باشد")
        return postal_code

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if not re.match(r'^09(\d{9})$', phone_number):
            raise forms.ValidationError("شماره موبایل باید در فرمت صحیح وارد شود مثال: 09123456789")
        return phone_number

class SelectAddressForm(forms.Form):
    address = forms.ModelChoiceField(
        queryset=None,  # این در view تنظیم می‌شود
        label='انتخاب آدرس موجود',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['address'].queryset = Address.objects.filter(user=user)