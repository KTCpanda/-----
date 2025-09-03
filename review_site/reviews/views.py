# reviews/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.db.models import Q, Count, Prefetch
from django.contrib import messages
from .models import Store, Review, Reaction, UserProfile, Follow, Notification, Tag, Conversation, DirectMessage
from .forms import StoreForm, ReviewForm, UserProfileForm, UserForm, TagForm
from .dm_forms import DirectMessageForm
import base64
import io
from PIL import Image

# 店一覧
def store_list(request):
    query = request.GET.get('q')
    
    # prefetch_relatedとselect_relatedで関連オブジェクトを効率的に取得
    stores = Store.objects.select_related('created_by').prefetch_related('tags', 'reviews')
    
    if query:
        stores = stores.filter(
            Q(name__icontains=query) | 
            Q(address__icontains=query)
        )
    
    stores = stores.order_by('-created_at')
    
    # 各店舗の評価統計を計算
    for store in stores:
        rating_stats = {}
        reviews = store.reviews.all()
        total_reviews = reviews.count()
        
        # 評価統計を安全に計算
        try:
            for rating_value, rating_label in Review.RATING_CHOICES:
                count = reviews.filter(rating=rating_value).count()
                if count > 0:
                    rating_stats[rating_value] = {
                        'label': rating_label,
                        'count': count
                    }
            
            # 評価をカウント数でソートし、上位3つのみを取得
            sorted_ratings = sorted(rating_stats.items(), key=lambda x: x[1]['count'], reverse=True)
            store.rating_stats = dict(sorted_ratings[:3])
        except Exception as e:
            # エラーが発生した場合は空の統計を設定
            print(f"Error calculating rating stats for store {store.id}: {e}")
            store.rating_stats = {}
        
        store.total_reviews = total_reviews
    
    return render(request, 'reviews/store_list.html', {
        'stores': stores,
        'query': query
    })

# 店の詳細・レビュー投稿
def store_detail(request, store_id):
    store = get_object_or_404(Store, id=store_id)
    
    if request.method == 'POST':
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
    
    # レビューを取得
    reviews = store.reviews.all()
    
    # 各レビューの情報を計算
    for review in reviews:
        try:
            # リアクション数を計算
            review.good_count = review.reactions.filter(reaction_type='good').count()
            review.bad_count = review.reactions.filter(reaction_type='bad').count()
            review.question_count = review.reactions.filter(reaction_type='question').count()
            
            # 友達関係を確認
            if request.user.is_authenticated and request.user != review.user:
                is_following = Follow.objects.filter(follower=request.user, following=review.user).exists()
                is_followed_by = Follow.objects.filter(follower=review.user, following=request.user).exists()
                review.is_friend = is_following and is_followed_by
            else:
                review.is_friend = False
        except Exception as e:
            print(f"Error processing review {review.id}: {e}")
            review.good_count = 0
            review.bad_count = 0
            review.question_count = 0
            review.is_friend = False
    
    # 評価統計を構築
    rating_stats = {}
    try:
        for rating_value, rating_label in Review.RATING_CHOICES:
            count = reviews.filter(rating=rating_value).count()
            if count > 0:
                rating_stats[rating_value] = {
                    'label': rating_label,
                    'count': count
                }
        
        
        # カウント数でソート
        sorted_ratings = sorted(rating_stats.items(), key=lambda x: x[1]['count'], reverse=True)
        rating_stats = dict(sorted_ratings)
    except Exception as e:
        print(f"Error building rating stats: {e}")
        rating_stats = {}
    
    return render(request, 'reviews/store_detail.html', {
        'store': store, 
        'form': form, 
        'reviews': reviews,
        'rating_stats': rating_stats
    })

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
            form.save_m2m()  # ManyToManyフィールドを保存
            return redirect('store_list')
    else:
        form = StoreForm()
    return render(request, 'reviews/store_form.html', {'form': form})

# タグ作成
@login_required
def tag_new(request):
    if request.method == 'POST':
        form = TagForm(request.POST)
        if form.is_valid():
            tag = form.save(commit=False)
            tag.created_by = request.user
            tag.save()
            return redirect('tag_list')
    else:
        form = TagForm()
    return render(request, 'reviews/tag_form.html', {'form': form})

# タグ一覧
@login_required
def tag_list(request):
    tags = Tag.objects.all().order_by('name')
    return render(request, 'reviews/tag_list.html', {'tags': tags})

# タグAPI（JSON）
@login_required
def tags_api(request):
    tags = Tag.objects.all().order_by('name')
    tags_data = [
        {
            'id': tag.id,
            'name': tag.name,
            'color': tag.color
        }
        for tag in tags
    ]
    return JsonResponse(tags_data, safe=False)

# 店舗にタグを追加
@login_required
def add_tag_to_store(request, store_id):
    if request.method == 'POST':
        store = get_object_or_404(Store, id=store_id)
        
        # 店舗の作成者のみがタグを追加可能
        if store.created_by != request.user:
            return JsonResponse({
                'success': False,
                'message': 'この店舗にタグを追加する権限がありません'
            })
        
        tag_id = request.POST.get('tag_id')
        
        if tag_id:
            try:
                tag = Tag.objects.get(id=tag_id)
                store.tags.add(tag)
                
                # 現在のタグリストを返す
                current_tags = [
                    {
                        'id': t.id,
                        'name': t.name,
                        'color': t.color
                    }
                    for t in store.tags.all()
                ]
                
                return JsonResponse({
                    'success': True,
                    'tags': current_tags
                })
            except Tag.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'タグが見つかりません'
                })
        
        return JsonResponse({
            'success': False,
            'message': 'タグIDが指定されていません'
        })
    
    return JsonResponse({
        'success': False,
        'message': '無効なリクエストです'
    })

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
# reviews/views.py

@login_required
def store_edit(request, store_id):
    store = get_object_or_404(Store, id=store_id)
    
    # 登録した本人でなければ、店詳細ページにリダイレクト
    if store.created_by != request.user:
        return redirect('store_detail', store_id=store.id)
    
    if request.method == 'POST':
        form = StoreForm(request.POST, request.FILES, instance=store)
        if form.is_valid():
            # form.save() でコメントを含む全てのフィールドが保存されます
            store = form.save(commit=False)
            
            # 新しい画像がアップロードされた場合のみ画像データを更新
            if form.cleaned_data.get('image'):
                image_file = form.cleaned_data['image']
                img = Image.open(image_file)
                img = img.convert('RGB')
                img.thumbnail((800, 600), Image.Resampling.LANCZOS)
                
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=85)
                image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                store.image_data = image_base64
            
            store.save()
            form.save_m2m()  # タグを保存
            return redirect('store_detail', store_id=store.id)
    else:
        form = StoreForm(instance=store)
    
    return render(request, 'reviews/store_form.html', {
        'form': form, 
        'store': store, 
        'is_edit': True
    })

# ... (他のコード) ...

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

@login_required
def profile_view(request):
    """プロフィール表示・編集"""
    # プロフィールが存在しない場合は作成
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
        
        if profile_form.is_valid():
            # プロフィール画像の処理
            if 'avatar' in request.FILES:
                image_file = request.FILES['avatar']
                img = Image.open(image_file)
                img = img.convert('RGB')
                
                # 画像サイズを調整
                img.thumbnail((300, 300))
                
                # Base64に変換
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=85)
                img_data = base64.b64encode(buffer.getvalue()).decode()
                profile.avatar_data = img_data
            
            profile_form.save()
            messages.success(request, 'プロフィールが更新されました！')
            return redirect('profile')
    else:
        profile_form = UserProfileForm(instance=profile)
    
    return render(request, 'reviews/profile.html', {
        'profile_form': profile_form,
        'profile': profile
    })

def user_profile_view(request, user_id):
    """他のユーザーのプロフィール表示"""
    profile_user = get_object_or_404(User, id=user_id)
    profile, created = UserProfile.objects.get_or_create(user=profile_user)
    
    # フォロー状況を確認
    is_following = False
    is_followed_by = False
    is_friend = False
    
    if request.user.is_authenticated:
        is_following = Follow.objects.filter(follower=request.user, following=profile_user).exists()
        is_followed_by = Follow.objects.filter(follower=profile_user, following=request.user).exists()
        is_friend = is_following and is_followed_by  # 相互フォローの場合は友達
    
    # ユーザーの投稿した店舗とレビューを取得
    user_stores = Store.objects.filter(created_by=profile_user).order_by('-created_at')[:5]
    user_reviews = Review.objects.filter(user=profile_user).order_by('-created_at')[:5]
    
    # フォロワー・フォロー数を取得
    followers_count = Follow.objects.filter(following=profile_user).count()
    following_count = Follow.objects.filter(follower=profile_user).count()
    
    return render(request, 'reviews/user_profile.html', {
        'profile_user': profile_user,
        'profile': profile,
        'is_following': is_following,
        'is_followed_by': is_followed_by,
        'is_friend': is_friend,
        'user_stores': user_stores,
        'user_reviews': user_reviews,
        'followers_count': followers_count,
        'following_count': following_count,
    })

@login_required
def follow_user(request, user_id):
    """ユーザーをフォロー/アンフォロー"""
    if request.method == 'POST':
        target_user = get_object_or_404(User, id=user_id)
        
        # 自分自身をフォローしようとした場合
        if target_user == request.user:
            return JsonResponse({'success': False, 'message': '自分自身をフォローすることはできません。'})
        
        follow_obj, created = Follow.objects.get_or_create(
            follower=request.user,
            following=target_user
        )
        
        if created:
            # フォロー通知を作成
            Notification.objects.create(
                user=target_user,
                from_user=request.user,
                notification_type='follow',
                message=f'{request.user.username}があなたをフォローしました。'
            )
            action = 'followed'
            message = f'{target_user.username}をフォローしました。'
        else:
            # 既にフォローしている場合はアンフォロー
            follow_obj.delete()
            action = 'unfollowed'
            message = f'{target_user.username}のフォローを解除しました。'
        
        # フォロワー数を更新
        followers_count = Follow.objects.filter(following=target_user).count()
        
        # 友達状態を確認
        is_following = Follow.objects.filter(follower=request.user, following=target_user).exists()
        is_followed_by = Follow.objects.filter(follower=target_user, following=request.user).exists()
        is_friend = is_following and is_followed_by
        
        return JsonResponse({
            'success': True,
            'action': action,
            'message': message,
            'followers_count': followers_count,
            'is_following': is_following,
            'is_friend': is_friend
        })
    
    return JsonResponse({'success': False, 'message': '無効なリクエストです。'})

@login_required
def notifications_view(request):
    """通知一覧（最適化版）"""
    # 未読通知を効率的に取得・処理
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False)
    unread_count = unread_notifications.count()
    
    if unread_count > 0:
        # 一括で既読にして削除
        unread_notifications.update(is_read=True)
        unread_notifications.delete()
        confirmation_message = f"{unread_count}件の通知を確認しました。"
    else:
        confirmation_message = None
    
    # 残りの通知（基本的に空）
    remaining_notifications = Notification.objects.filter(user=request.user)
    
    return render(request, 'reviews/notifications.html', {
        'notifications': remaining_notifications,
        'had_unread': unread_count > 0,
        'confirmation_message': confirmation_message
    })

@login_required
def get_unread_notifications_count(request):
    """未読通知数を取得"""
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'count': count})

@login_required
def remove_tag_from_store(request, store_id):
    """店舗からタグを削除"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'POST method required'}, status=405)
    
    store = get_object_or_404(Store, id=store_id)
    
    # 店舗の作成者のみが削除可能
    if store.created_by != request.user:
        return JsonResponse({'success': False, 'message': '権限がありません'}, status=403)
    
    tag_id = request.POST.get('tag_id')
    if not tag_id:
        return JsonResponse({'success': False, 'message': 'タグIDが必要です'}, status=400)
    
    try:
        tag = Tag.objects.get(id=tag_id)
        store.tags.remove(tag)
        return JsonResponse({
            'success': True,
            'message': 'タグが削除されました'
        })
    except Tag.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'タグが見つかりません'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@login_required
def user_list(request):
    # 全ユーザーを取得
    all_users = User.objects.select_related('profile').order_by('username')
    
    # 現在のユーザーがフォローしているユーザーのIDリスト
    following_ids = set(Follow.objects.filter(follower=request.user).values_list('following_id', flat=True))
    
    # 現在のユーザーをフォローしているユーザーのIDリスト
    followers_ids = set(Follow.objects.filter(following=request.user).values_list('follower_id', flat=True))

    users_with_status = []
    for user in all_users:
        is_following = user.id in following_ids
        is_followed_by = user.id in followers_ids
        is_friend = is_following and is_followed_by
        
        users_with_status.append({
            'user': user,
            'is_following': is_following,
            'is_friend': is_friend,
        })

    return render(request, 'reviews/user_list.html', {'users_with_status': users_with_status})

@login_required
def send_dm(request, user_id):
    """DMの会話画面とメッセージ送信"""
    recipient = get_object_or_404(User, id=user_id)
    
    # 自分自身には送信できない
    if recipient == request.user:
        return redirect('user_list')

    # 2人のユーザーを含む会話を取得または作成
    conversation = Conversation.objects.filter(participants=request.user).filter(participants=recipient).first()
    if not conversation:
        conversation = Conversation.objects.create()
        conversation.participants.add(request.user, recipient)

    if request.method == 'POST':
        form = DirectMessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.conversation = conversation
            message.sender = request.user
            message.save()
            # POST後は同じページにリダイレクトしてフォームの再送信を防ぐ
            return redirect('send_dm', user_id=recipient.id)
    else:
        form = DirectMessageForm()

    # 会話のメッセージを取得
    messages = conversation.messages.all().order_by('created_at')

    # テンプレートをレンダリング
    return render(request, 'reviews/dm_conversation.html', {
        'recipient': recipient,
        'conversation': conversation,
        'messages': messages,
        'form': form,
    })
