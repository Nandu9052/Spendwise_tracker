from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from decimal import Decimal
import datetime

from .models import Category, Budget, Expense


class RegistrationForm(UserCreationForm):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Choose a username',
            'autocomplete': 'username',
        })
    )
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Create a password',
            'id': 'id_password1',
            'autocomplete': 'new-password',
        })
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Confirm your password',
            'id': 'id_password2',
            'autocomplete': 'new-password',
        })
    )

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'e.g. Food, Transport, Shopping',
                'maxlength': '100',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Brief description of this category (optional)',
                'rows': 3,
                'maxlength': '500',
            }),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise ValidationError('Category name is required.')
        # Check uniqueness for this user
        qs = Category.objects.filter(user=self.user, name__iexact=name)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError('You already have a category with this name.')
        return name


class BudgetForm(forms.ModelForm):
    month_year = forms.CharField(
        widget=forms.DateInput(attrs={
            'class': 'form-control form-control-lg',
            'type': 'month',
        }),
        help_text='Select month and year'
    )

    class Meta:
        model = Budget
        fields = ['category', 'month_year', 'monthly_limit']
        widgets = {
            'category': forms.Select(attrs={
                'class': 'form-select form-select-lg',
            }),
            'monthly_limit': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': '0.00',
                'min': '0.01',
                'step': '0.01',
            }),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        if user:
            self.fields['category'].queryset = Category.objects.filter(user=user)
        # Pre-populate month_year field for existing instances
        if self.instance and self.instance.pk and self.instance.month_year:
            self.initial['month_year'] = self.instance.month_year.strftime('%Y-%m')

    def clean_monthly_limit(self):
        amount = self.cleaned_data.get('monthly_limit')
        if amount is not None and amount <= Decimal('0'):
            raise ValidationError('Monthly limit must be greater than ₹0.')
        return amount

    def clean_month_year(self):
        raw = self.cleaned_data.get('month_year', '')
        if not raw:
            raise ValidationError('Please select a month.')
        # Accept both YYYY-MM and YYYY-MM-DD formats
        raw = raw.strip()
        try:
            if len(raw) == 7:  # YYYY-MM
                year, month = map(int, raw.split('-'))
            elif len(raw) >= 10:  # YYYY-MM-DD
                parts = raw.split('-')
                year, month = int(parts[0]), int(parts[1])
            else:
                raise ValueError("Bad format")
            if not (1 <= month <= 12):
                raise ValidationError('Invalid month.')
            return datetime.date(year, month, 1)
        except (ValueError, TypeError):
            raise ValidationError('Enter a valid month (YYYY-MM).')

    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get('category')
        month_year = cleaned_data.get('month_year')
        if category and month_year and self.user:
            qs = Budget.objects.filter(
                user=self.user,
                category=category,
                month_year=month_year
            )
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(
                    f'A budget for "{category.name}" in {month_year.strftime("%B %Y")} already exists.'
                )
        return cleaned_data


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['amount', 'date', 'category', 'notes']
        widgets = {
            'amount': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': '0.00',
                'min': '0.01',
                'step': '0.01',
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control form-control-lg',
                'type': 'date',
            }),
            'category': forms.Select(attrs={
                'class': 'form-select form-select-lg',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Optional notes about this expense',
                'rows': 3,
            }),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        if user:
            self.fields['category'].queryset = Category.objects.filter(user=user)
        # Default date to today
        if not self.instance.pk:
            self.fields['date'].initial = datetime.date.today()

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount <= Decimal('0'):
            raise ValidationError('Amount must be greater than ₹0.')
        return amount

    def clean_category(self):
        category = self.cleaned_data.get('category')
        if category and self.user:
            if category.user != self.user:
                raise ValidationError('Invalid category selection.')
        return category
