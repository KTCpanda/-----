from pathlib import Path
import os
import dj_database_url
import cloudinary
import cloudinary.uploader
import cloudinary.api
from dotenv import load_dotenv

# .envファイルを読み込む
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# --- 本番環境用の設定 ---
# SECRET_KEYは環境変数から読み込む
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-2j#d1(m91f@8z05j^h(%=b*hr7$a8ow_28-#99!exvd*awir@g')

# DEBUGモードは環境変数から読み込む
DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'

# Renderのドメインを許可（ローカル開発時も含む）
ALLOWED_HOSTS = ['.onrender.com', '127.0.0.1', 'localhost']

# --- アプリケーション定義 ---
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'reviews',
    'whitenoise.runserver_nostatic', # WhiteNoiseを追加
    'cloudinary_storage',
    'cloudinary',
]

# --- ミドルウェア設定 ---
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # WhiteNoiseを一番上に近い位置に追加
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'review_site.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'review_site.wsgi.application'


# --- データベース設定 ---
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL'),
        conn_max_age=600
    )
}


# --- パスワード検証 ---
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --- 国際化設定 ---
LANGUAGE_CODE = 'ja'
TIME_ZONE = 'Asia/Tokyo'
USE_I18N = True
USE_TZ = True

# --- 静的ファイル (CSS, JavaScript) の設定 ---
STATIC_URL = 'static/'
# ★★★ この行を修正しました ★★★
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = BASE_DIR / 'staticfiles' # collectstaticの出力先
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# --- メディアファイル (画像アップロード) の設定 ---
# Cloudinary設定
cloudinary.config(
    cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
    api_key=os.environ.get('CLOUDINARY_API_KEY'),
    api_secret=os.environ.get('CLOUDINARY_API_SECRET'),
    secure=True
)

# メディアファイルはCloudinaryを使用
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
MEDIA_URL = '/media/'


# --- 主キーの型設定 ---
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- ログイン・ログアウトのリダイレクト設定 ---
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# --- ホットペッパーAPIキーの設定（必要に応じて追加） ---
HOTPEPPER_API_KEY = os.environ.get('HOTPEPPER_API_KEY', '')
