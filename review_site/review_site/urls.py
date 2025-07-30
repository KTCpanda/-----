from django.contrib import admin
from django.urls import path, include

# --- 画像表示のために必須のimport ---
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('reviews.urls')),
]

# --- 画像表示のために必須の設定 ---
# 開発サーバーで動かしている時(DEBUG=True)にのみ、この設定を有効にする
if settings.DEBUG:
    # /media/ というURLでリクエストが来た時に、
    # MEDIA_ROOT (mediaフォルダ) の中からファイルを探すように道案内を追加する
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
