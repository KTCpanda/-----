# reviews/models.py
from django.db import models
from django.contrib.auth.models import User
import base64
import io
from PIL import Image

class UserProfile(models.Model):
    user = models.OneToOneField(User, verbose_name="ユーザー", on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField("自己紹介", blank=True, null=True, max_length=500)
    avatar_data = models.TextField("プロフィール画像（Base64）", blank=True, null=True)
    location = models.CharField("住所", max_length=100, blank=True, null=True)
    birth_date = models.DateField("生年月日", blank=True, null=True)
    created_at = models.DateTimeField("作成日", auto_now_add=True)
    updated_at = models.DateTimeField("更新日", auto_now=True)

    def __str__(self):
        return f"{self.user.username}のプロフィール"
    
    def get_avatar_url(self):
        """Base64画像データをdata URLとして返す"""
        if self.avatar_data:
            return f"data:image/jpeg;base64,{self.avatar_data}"
        return None

class Follow(models.Model):
    follower = models.ForeignKey(User, verbose_name="フォローする人", on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(User, verbose_name="フォローされる人", on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField("フォロー日", auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'following')
        
    def __str__(self):
        return f"{self.follower.username} → {self.following.username}"

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('follow', 'フォロー'),
        ('review', 'レビュー'),
        ('reaction', 'リアクション'),
    ]
    
    user = models.ForeignKey(User, verbose_name="通知を受け取る人", on_delete=models.CASCADE, related_name='notifications')
    from_user = models.ForeignKey(User, verbose_name="通知を送る人", on_delete=models.CASCADE, related_name='sent_notifications')
    notification_type = models.CharField("通知タイプ", max_length=20, choices=NOTIFICATION_TYPES)
    message = models.TextField("通知内容")
    is_read = models.BooleanField("既読", default=False)
    created_at = models.DateTimeField("通知日", auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.from_user.username}から{self.user.username}への{self.get_notification_type_display()}"

# ... Storeモデルは変更なし ...
class Store(models.Model):
    name = models.CharField("店名", max_length=100)
    address = models.CharField("住所", max_length=200)
    image_data = models.TextField("お店の画像（Base64）", blank=True, null=True)
    created_by = models.ForeignKey(User, verbose_name="登録者", on_delete=models.CASCADE)
    tags = models.ManyToManyField('Tag', verbose_name="タグ", blank=True)
    comment = models.TextField("コメント", blank=True, null=True)
    website_url = models.URLField("公式サイトURL", blank=True, null=True)
    created_at = models.DateTimeField("登録日", auto_now_add=True)

    def __str__(self):
        return self.name
    
    def get_image_url(self):
        """Base64画像データをdata URLとして返す"""
        if self.image_data:
            return f"data:image/jpeg;base64,{self.image_data}"
        return None

# タグモデル
class Tag(models.Model):
    COLOR_CHOICES = [
        ('#FF6B6B', '赤'),
        ('#4ECDC4', '青緑'),
        ('#45B7D1', '青'),
        ('#96CEB4', '緑'),
        ('#FFEAA7', '黄'),
        ('#DDA0DD', '紫'),
        ('#F39C12', 'オレンジ'),
        ('#E17055', '茶'),
        ('#74B9FF', '水色'),
        ('#FD79A8', 'ピンク'),
    ]
    
    name = models.CharField("タグ名", max_length=50, unique=True)
    color = models.CharField("色", max_length=7, choices=COLOR_CHOICES, default='#4ECDC4')
    created_by = models.ForeignKey(User, verbose_name="作成者", on_delete=models.CASCADE)
    created_at = models.DateTimeField("作成日", auto_now_add=True)
    
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

class Reaction(models.Model):
    REACTION_CHOICES = [
        ('good', '👍 ぐっと'),
        ('bad', '👎 のっと'),
        ('question', '❓ ？'),
    ]

    review = models.ForeignKey(Review, verbose_name="レビュー", on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(User, verbose_name="リアクションした人", on_delete=models.CASCADE)
    reaction_type = models.CharField("リアクション", max_length=20, choices=REACTION_CHOICES)
    created_at = models.DateTimeField("リアクション日", auto_now_add=True)

    class Meta:
        unique_together = ('review', 'user')  # 1つのレビューに対して1人1つのリアクションのみ

    def __str__(self):
        return f"{self.user.username}が{self.review}に{self.get_reaction_type_display()}"

class Conversation(models.Model):
    """
    ユーザー間の会話を表すモデル。
    参加者を2人に限定する。
    """
    participants = models.ManyToManyField(User, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        users = self.participants.all()
        if users.count() == 2:
            return f"Conversation between {users[0].username} and {users[1].username}"
        return f"Conversation {self.id}"

class DirectMessage(models.Model):
    """
    ダイレクトメッセージの内容を表すモデル。
    """
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField("メッセージ内容")
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"From {self.sender.username} at {self.created_at:%Y-%m-%d %H:%M}"