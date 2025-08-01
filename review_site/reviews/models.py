# reviews/models.py
from django.db import models
from django.contrib.auth.models import User

# ... Storeモデルは変更なし ...
class Store(models.Model):
    name = models.CharField("店名", max_length=100)
    address = models.CharField("住所", max_length=200)
    image = models.ImageField("お店の画像", upload_to='store_images/', blank=True, null=True)
    created_by = models.ForeignKey(User, verbose_name="登録者", on_delete=models.CASCADE)
    created_at = models.DateTimeField("登録日", auto_now_add=True)

    def __str__(self):
        return self.name

# reviews/models.py

# ... (前半のStoreモデルなどは変更なし) ...

class Review(models.Model):
    # ↓↓ この選択肢を書き換える ↓↓
    RATING_CHOICES = [
        (5, '😍 文句なしの大満足！'),
        (4, '✨ かなり良い'),
        (3, '🙂 まあまあ'),
        (2, '🤔 うーん…'),
        (1, '😩 がっかり…'),
    ]

    store = models.ForeignKey(Store, verbose_name="店", on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, verbose_name="投稿者", on_delete=models.CASCADE)
    rating = models.IntegerField("評価", choices=RATING_CHOICES, default=3)
    comment = models.TextField("コメント", blank=True, null=True)
    created_at = models.DateTimeField("投稿日", auto_now_add=True)

    def __str__(self):
        return f"{self.store.name}への{self.user.username}のレビュー"