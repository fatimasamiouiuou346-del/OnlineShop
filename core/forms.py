from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

# 获取当前项目实际使用的用户模型（即 core.User）
User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    # 添加这些字段让用户在注册时填写
    email = forms.EmailField(required=True, label="Email Address")
    full_name = forms.CharField(required=True, label="Full Name")

    class Meta:
        model = User
        # 指定表单中显示的字段
        fields = ("username", "email", "full_name")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.full_name = self.cleaned_data["full_name"]
        if commit:
            user.save()
        return user