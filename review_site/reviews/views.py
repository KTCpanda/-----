# reviews/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from .models import Store, Review
from .forms import StoreForm, ReviewForm

# 店一覧
def store_list(request):
    stores = Store.objects.all().order_by('-created_at')
    return render(request, 'reviews/store_list.html', {'stores': stores})

# 店の詳細・レビュー投稿
def store_detail(request, store_id):
    store = get_object_or_404(Store, id=store_id)
    if request.method == 'POST':
        # ログインしていない場合は処理しない
        if not request.user.is_authenticated:
            return redirect('login')
        
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.store = store
            review.user = request.user
            review.save()
            return redirect('store_detail', store_id=store.id)
    else:
        form = ReviewForm()
    return render(request, 'reviews/store_detail.html', {'store': store, 'form': form})

# 店の登録
@login_required
def store_new(request):
    if request.method == 'POST':
        # ↓↓ この行を修正します ↓↓
        form = StoreForm(request.POST, request.FILES)
        if form.is_valid():
            store = form.save(commit=False)
            store.created_by = request.user
            store.save()
            return redirect('store_list')
    else:
        form = StoreForm()
    return render(request, 'reviews/store_form.html', {'form': form})

# ユーザー登録
def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'reviews/signup.html', {'form': form})

@login_required
def review_delete(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    
    # ログイン中のユーザーがコメントの投稿者であるかを確認
    if request.user == review.user:
        # POSTリクエストの場合のみ削除を実行 (安全のため)
        if request.method == 'POST':
            store_id = review.store.id  # 削除後に戻るため、店のIDを先に取得
            review.delete()
            return redirect('store_detail', store_id=store_id)
            
    # 条件に合わない場合は、元の店の詳細ページにリダイレクト
    return redirect('store_detail', store_id=review.store.id)

@login_required
def store_delete(request, store_id):
    store = get_object_or_404(Store, id=store_id)
    
    # 登録した本人でなければ、店一覧ページにリダイレクト
    if store.created_by != request.user:
        return redirect('store_list')

    # POSTリクエストの場合のみ削除を実行
    if request.method == 'POST':
        store.delete()
        return redirect('store_list')
    
    # GETリクエストの場合は、確認ページを表示
    # この確認ページはレビュー削除と共用できます
    return render(request, 'reviews/delete_confirm.html', {'object': store})
