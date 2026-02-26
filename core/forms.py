from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.forms import inlineformset_factory
from .models import Product, Order, ProductImage

User = get_user_model()

# ==========================================
# 1. 用户注册表单 (Block A1)
# ==========================================
class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Email Address")
    full_name = forms.CharField(required=True, label="Full Name")
    address = forms.CharField(required=True, label="Shipping Address", widget=forms.Textarea(attrs={'rows': 3}))
    city = forms.CharField(required=True, label="City")
    
    class Meta:
        model = User
        fields = ("username", "email", "full_name")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.full_name = self.cleaned_data["full_name"]
        if commit:
            user.save()
            from .models import Address
            Address.objects.create(
                user=user,
                recipient_name=user.full_name,
                address_line1=self.cleaned_data["address"],
                city=self.cleaned_data["city"],
                zip_code="000000", 
                country="Macau" 
            )
        return user

# ==========================================
# 2. 商家管理表单 (Vendor Portal)
# ==========================================
class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['category', 'name', 'brand', 'material', 'origin', 'video', 'description_html', 'price', 'stock_quantity', 'is_active']
        widgets = {
            'description_html': forms.Textarea(attrs={'rows': 4}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'video': forms.FileInput(attrs={'class': 'form-control', 'accept': 'video/*'})
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-control'})

class OrderStatusForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'})
        }

# ==========================================
# 3. 多图管理表单集 (Block B1)
# ==========================================
class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ['image', 'is_primary']
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'is_primary': forms.CheckboxInput(attrs={'class': 'form-check-input is-primary-checkbox'}),
        }

ProductImageFormSet = inlineformset_factory(
    Product, 
    ProductImage, 
    form=ProductImageForm,
    fields=['image', 'is_primary'],
    extra=3, 
    can_delete=True
)
