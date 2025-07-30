from django.contrib import admin
from django.urls import path, include

# ↓↓ この2行がimportされているか確認・追加 ↓↓
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('reviews.urls')),
]

# ↓↓ このif文がファイルの一番下にあるか確認・追加 ↓↓
# 開発環境でメディアファイル（アップロードされた画像）を提供するための設定
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)