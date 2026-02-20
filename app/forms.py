from django import forms
from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile, Product, DeliveryArea, ShippingAddress, Category, Review

class UserRegistrationForm(UserCreationForm):
    ROLE_CHOICES = (
        ('buyer', 'Buyer'),
        ('seller', 'Seller'),
    )
    role = forms.ChoiceField(choices=ROLE_CHOICES, widget=forms.RadioSelect, initial='buyer')

    class Meta:
        model = User
        fields = ['username', 'email', 'role']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.help_text = None
        self.fields['email'].required = True
        field_order = ['username', 'email', 'role', 'password1', 'password2']
        self.fields = {key: self.fields[key] for key in field_order if key in self.fields}
        if 'role' in self.fields:
            self.fields['role'].required = True

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            profile, created = Profile.objects.get_or_create(user=user)
            role = self.cleaned_data.get('role')
            if role:
                profile.role = role
                profile.save()
        return user

class CustomPasswordResetForm(forms.Form):
    identifier = forms.CharField(
        label='Username or Email',
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Enter your username or email'})
    )

    def clean(self):
        cleaned_data = super().clean()
        identifier = cleaned_data.get('identifier', '').strip()

        if identifier:
            user = User.objects.filter(models.Q(username__iexact=identifier) | models.Q(email__iexact=identifier)).first()
            if not user:
                raise forms.ValidationError(
                    "No account found with that username or email."
                )
            self.user_cache = user
        return cleaned_data

    def get_user(self):
        return getattr(self, 'user_cache', None)

class ProductForm(forms.ModelForm):
    category = forms.ModelChoiceField(
        queryset=None,
        widget=forms.Select(attrs={
            'class': 'form-input',
            'style': 'background: var(--bg-surface); border: 1px solid rgba(255,255,255,0.1); padding: 15px; border-radius: 12px; color: white; margin-bottom: 20px;',
            'id': 'category-select'
        }),
        empty_label="-- Select a Category or Create New --",
        required=False
    )

    new_category = forms.CharField(
        label='Or Create New Category',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter new category name (e.g., Electronics, Books)',
            'style': 'background: var(--bg-surface); border: 1px solid rgba(255,255,255,0.1); padding: 15px; border-radius: 12px; color: white; margin-bottom: 20px;'
        })
    )

    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'image', 'category', 'gender', 'stock_count', 'size']
        widgets = {
            'gender': forms.Select(attrs={
                'class': 'form-input',
                'style': 'background: var(--bg-surface); border: 1px solid rgba(255,255,255,0.1); padding: 15px; border-radius: 12px; color: white; margin-bottom: 20px; width: 100%;'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Product Name',
                'style': 'background: var(--bg-surface); border: 1px solid rgba(255,255,255,0.1); padding: 15px; border-radius: 12px; color: white; margin-bottom: 20px;'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-input',
                'placeholder': 'Product Description',
                'rows': 5,
                'style': 'background: var(--bg-surface); border: 1px solid rgba(255,255,255,0.1); padding: 15px; border-radius: 12px; color: white; margin-bottom: 20px; resize: vertical;'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Price',
                'step': '0.01',
                'style': 'background: var(--bg-surface); border: 1px solid rgba(255,255,255,0.1); padding: 15px; border-radius: 12px; color: white; margin-bottom: 20px;'
            }),
            'stock_count': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Stock Count',
                'min': '1',
                'style': 'background: var(--bg-surface); border: 1px solid rgba(255,255,255,0.1); padding: 15px; border-radius: 12px; color: white; margin-bottom: 20px;'
            }),
            'size': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Available Sizes (e.g., XS, S, M, L, XL or enter custom sizes separated by commas)',
                'style': 'background: var(--bg-surface); border: 1px solid rgba(255,255,255,0.1); padding: 15px; border-radius: 12px; color: white; margin-bottom: 20px;'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-input',
                'accept': 'image/*',
                'style': 'background: var(--bg-surface); border: 1px solid rgba(255,255,255,0.1); padding: 15px; border-radius: 12px; color: white; margin-bottom: 20px;'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import Category
        self.fields['category'].queryset = Category.objects.all()

    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get('category')
        new_category = cleaned_data.get('new_category', '').strip()
        existing_category = getattr(getattr(self, 'instance', None), 'category', None)
        if not category and not new_category and not existing_category:
            raise forms.ValidationError(
                "Please either select an existing category or enter a new category name."
            )
        if new_category:
            from .models import Category
            if Category.objects.filter(name__iexact=new_category).exists():
                raise forms.ValidationError(
                    f"Category '{new_category}' already exists. Please select it from the list."
                )
        return cleaned_data

class DeliveryAreaForm(forms.ModelForm):
    class Meta:
        model = DeliveryArea
        fields = ['pincode', 'is_active', 'estimated_days']

class ShippingAddressForm(forms.ModelForm):
    class Meta:
        model = ShippingAddress
        fields = ['full_name', 'address_line_1', 'address_line_2', 'city', 'state', 'pincode', 'phone_number']
        widgets = {
            field: forms.TextInput(attrs={'class': 'form-input', 'style': 'background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.1); padding: 12px; border-radius: 8px; color: white; width: 100%; margin-bottom: 15px;'})
            for field in ['full_name', 'address_line_1', 'address_line_2', 'city', 'state', 'pincode', 'phone_number']
        }

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'icon']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Category Name (e.g., Electronics, Clothing)',
                'style': 'background: var(--bg-surface); border: 1px solid rgba(255,255,255,0.1); padding: 15px; border-radius: 12px; color: white; margin-bottom: 20px;'
            }),
            'icon': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'FontAwesome Icon (e.g., fa-laptop, fa-shirt, fa-book)',
                'style': 'background: var(--bg-surface); border: 1px solid rgba(255,255,255,0.1); padding: 15px; border-radius: 12px; color: white; margin-bottom: 20px;'
            }),
        }

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.RadioSelect(choices=[(i, f'{i} Star{"s" if i != 1 else ""}') for i in range(1, 6)], attrs={
                'class': 'form-input',
                'style': 'margin-bottom: 20px;'
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-input',
                'placeholder': 'Share your experience with this product...',
                'rows': 4,
                'style': 'background: var(--bg-surface); border: 1px solid rgba(255,255,255,0.1); padding: 15px; border-radius: 12px; color: white; margin-bottom: 20px; resize: vertical;'
            }),
        }
