# reviews/forms.py
from django import forms
from .models import DirectMessage

class DirectMessageForm(forms.ModelForm):
    class Meta:
        model = DirectMessage
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'メッセージを入力...',
            }),
        }
