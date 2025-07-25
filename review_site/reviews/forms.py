# reviews/forms.py
from django import forms
from .models import Store, Review

# ... StoreFormは変更なし ...
class StoreForm(forms.ModelForm):
    class Meta:
        model = Store
        fields = ['name', 'address', 'image']


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        # ↓↓ widgetの設定を追加 ↓↓
        widgets = {
            'rating': forms.RadioSelect(attrs={'class': 'rating-radio'}),
        }