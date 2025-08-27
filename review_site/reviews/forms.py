# reviews/forms.py
from django import forms
from django.contrib.auth.models import User
from .models import Store, Review, UserProfile, Tag

# タグフォーム
class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ['name', 'color']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'タグ名を入力'}),
            'color': forms.Select(attrs={'class': 'color-select'}),
        }

# ... StoreFormは変更なし ...
class StoreForm(forms.ModelForm):
    image = forms.ImageField(label="お店の画像", required=False)
    
    class Meta:
        model = Store
        fields = ['name', 'address', 'tags', 'image', 'comment', 'website_url']
        widgets = {
            'tags': forms.CheckboxSelectMultiple(),
            'comment': forms.Textarea(attrs={'rows': 4, 'placeholder': 'お店についてのコメントを入力...'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # タグの選択肢を設定
        self.fields['tags'].queryset = Tag.objects.all()
        self.fields['tags'].required = False


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        # ↓↓ widgetの設定を追加 ↓↓
        widgets = {
            'rating': forms.RadioSelect(attrs={'class': 'rating-radio'}),
        }

class UserProfileForm(forms.ModelForm):
    avatar = forms.ImageField(label="プロフィール画像", required=False, widget=forms.FileInput(attrs={'style': 'display: none;', 'id': 'avatar-input'}))
    
    # 年、月、日の選択肢を作成
    YEAR_CHOICES = [(year, year) for year in range(1950, 2025)]
    MONTH_CHOICES = [(month, month) for month in range(1, 13)]
    DAY_CHOICES = [(day, day) for day in range(1, 32)]
    
    birth_year = forms.ChoiceField(choices=[('', '年')] + YEAR_CHOICES, required=False)
    birth_month = forms.ChoiceField(choices=[('', '月')] + MONTH_CHOICES, required=False)
    birth_day = forms.ChoiceField(choices=[('', '日')] + DAY_CHOICES, required=False)
    
    class Meta:
        model = UserProfile
        fields = ['bio', 'birth_date', 'avatar']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4, 'placeholder': '自己紹介を入力してください...'}),
            'birth_date': forms.HiddenInput(),  # 隠しフィールドとして保持
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 既存の誕生日データがある場合、各フィールドに分割
        if self.instance.birth_date:
            self.fields['birth_year'].initial = self.instance.birth_date.year
            self.fields['birth_month'].initial = self.instance.birth_date.month
            self.fields['birth_day'].initial = self.instance.birth_date.day
    
    def clean(self):
        cleaned_data = super().clean()
        year = cleaned_data.get('birth_year')
        month = cleaned_data.get('birth_month')
        day = cleaned_data.get('birth_day')
        
        # 年、月、日がすべて入力されている場合のみ日付を作成
        if year and month and day:
            try:
                from datetime import date
                birth_date = date(int(year), int(month), int(day))
                cleaned_data['birth_date'] = birth_date
            except ValueError:
                raise forms.ValidationError("有効な日付を入力してください。")
        else:
            cleaned_data['birth_date'] = None
        
        return cleaned_data

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = []  # 姓名を削除