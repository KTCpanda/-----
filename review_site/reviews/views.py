# reviews/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from .models import Store, Review, Reaction
from .forms import StoreForm, ReviewForm
import base64
import io
from PIL import Image

# 店一覧
def store_list(request):
    query = request.GET.get('q')
    stores = Store.objects.all()
    
    if query:
        stores = stores.filter(
            Q(name__icontains=query) | 
            Q(address__icontains=query)
        )
    
    stores = stores.order_by('-created_at')
    return render(request, 'reviews/store_list.html', {
        'stores': stores,
        'query': query
    })

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
    
    # 各レビューにリアクション数を追加
    reviews = store.reviews.all()
    for review in reviews:
        review.good_count = review.reactions.filter(reaction_type='good').count()
        review.bad_count = review.reactions.filter(reaction_type='bad').count()
        review.question_count = review.reactions.filter(reaction_type='question').count()
    
    return render(request, 'reviews/store_detail.html', {'store': store, 'form': form, 'reviews': reviews})

# 店の登録
@login_required
def store_new(request):
    if request.method == 'POST':
        form = StoreForm(request.POST, request.FILES)
        if form.is_valid():
            store = form.save(commit=False)
            store.created_by = request.user
            
            # 画像をBase64に変換して保存
            if form.cleaned_data['image']:
                image_file = form.cleaned_data['image']
                # 画像をリサイズ
                img = Image.open(image_file)
                img = img.convert('RGB')
                img.thumbnail((800, 600), Image.Resampling.LANCZOS)
                
                # Base64に変換
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=85)
                image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                store.image_data = image_base64
            
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
def store_edit(request, store_id):
    store = get_object_or_404(Store, id=store_id)
    
    # 登録した本人でなければ、店詳細ページにリダイレクト
    if store.created_by != request.user:
        return redirect('store_detail', store_id=store.id)
    
    if request.method == 'POST':
        form = StoreForm(request.POST, request.FILES)
        if form.is_valid():
            store.name = form.cleaned_data['name']
            store.address = form.cleaned_data['address']
            
            # 新しい画像がアップロードされた場合
            if form.cleaned_data['image']:
                image_file = form.cleaned_data['image']
                img = Image.open(image_file)
                img = img.convert('RGB')
                img.thumbnail((800, 600), Image.Resampling.LANCZOS)
                
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=85)
                image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                store.image_data = image_base64
            
            store.save()
            return redirect('store_detail', store_id=store.id)
    else:
        form = StoreForm(initial={'name': store.name, 'address': store.address})
    
    return render(request, 'reviews/store_form.html', {
        'form': form, 
        'store': store, 
        'is_edit': True
    })

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

@login_required
def add_reaction(request, review_id):
    """レビューにリアクションを追加する"""
    if request.method != 'POST':
        return JsonResponse({'error': '不正なリクエストです'}, status=400)
    
    review = get_object_or_404(Review, id=review_id)
    reaction_type = request.POST.get('reaction_type')
    
    if reaction_type not in ['good', 'bad', 'question']:
        return JsonResponse({'error': '不正なリアクションです'}, status=400)
    
    # 既存のリアクションを削除して新しいリアクションを追加（または同じなら削除）
    existing_reaction = Reaction.objects.filter(review=review, user=request.user).first()
    
    if existing_reaction:
        if existing_reaction.reaction_type == reaction_type:
            # 同じリアクションなら削除（取り消し）
            existing_reaction.delete()
            action = 'removed'
        else:
            # 違うリアクションなら更新
            existing_reaction.reaction_type = reaction_type
            existing_reaction.save()
            action = 'updated'
    else:
        # 新しいリアクションを作成
        Reaction.objects.create(
            review=review,
            user=request.user,
            reaction_type=reaction_type
        )
        action = 'added'
    
    # 各リアクションの数を取得
    reaction_counts = {
        'good': review.reactions.filter(reaction_type='good').count(),
        'bad': review.reactions.filter(reaction_type='bad').count(),
        'question': review.reactions.filter(reaction_type='question').count(),
    }
    
    return JsonResponse({
        'action': action,
        'reaction_counts': reaction_counts
    })

@login_required
def get_user_reaction(request, review_id):
    """ユーザーの現在のリアクション状態を取得"""
    review = get_object_or_404(Review, id=review_id)
    user_reaction = Reaction.objects.filter(review=review, user=request.user).first()
    
    if user_reaction:
        return JsonResponse({'user_reaction': user_reaction.reaction_type})
    else:
        return JsonResponse({'user_reaction': None})
