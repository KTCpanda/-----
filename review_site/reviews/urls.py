# reviews/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # ホームページ（店一覧）
    path('', views.store_list, name='store_list'),
    
    # 店の詳細ページ
    path('store/<int:store_id>/', views.store_detail, name='store_detail'),
    
    # 店の登録ページ
    path('store/new/', views.store_new, name='store_new'),
    
    # 店の編集ページ
    path('store/<int:store_id>/edit/', views.store_edit, name='store_edit'),

    # ユーザー認証
    path('signup/', views.signup, name='signup'),
    # reviews/urls.py
    path('login/', auth_views.LoginView.as_view(template_name='reviews/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('review/<int:review_id>/delete/', views.review_delete, name='review_delete'),
    path('store/<int:store_id>/delete/', views.store_delete, name='store_delete'),
    
    # リアクション機能
    path('review/<int:review_id>/reaction/', views.add_reaction, name='add_reaction'),
]