from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('reviews.urls')),
]

# Cloudinaryを使用するため、ローカルメディアファイル配信は不要
