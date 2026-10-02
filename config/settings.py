"""
Django settings for Darabi Studio.
Production-ready: reads secrets/config from environment variables (.env locally).
"""
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

def env_bool(key, default=False):
    return os.environ.get(key, str(default)).lower() in ("1", "true", "yes")

# ---- Core ----
SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-CHANGE-ME-before-going-live")
DEBUG = env_bool("DEBUG", True)
ALLOWED_HOSTS = [h.strip() for h in os.environ.get("ALLOWED_HOSTS", "127.0.0.1,localhost").split(",") if h.strip()]
SITE_URL = os.environ.get("SITE_URL", "http://127.0.0.1:8000")

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.sitemaps',
    'store',
]
SITE_ID = 1

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'store.context_processors.site_settings',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# ---- Database ----
# Uses DATABASE_URL if provided (Postgres in production), else falls back to local SQLite.
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL:
    import dj_database_url
    DATABASES = {"default": dj_database_url.parse(DATABASE_URL, conn_max_age=600)}
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Karachi'
USE_I18N = True
USE_TZ = True

# ---- Static & Media ----
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
}

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Optional: Cloudinary for product image hosting (recommended for production —
# local media files are usually wiped on redeploy by free hosts).
# Set CLOUDINARY_URL env var to enable; falls back to local disk storage otherwise.
if os.environ.get("CLOUDINARY_URL"):
    INSTALLED_APPS += ['cloudinary_storage', 'cloudinary']
    STORAGES["default"] = {"BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage"}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ---- Email (order notifications) ----
# Defaults to printing emails to the console in dev. Set EMAIL_HOST etc. in
# .env for real delivery (e.g. Gmail SMTP, SendGrid, Mailgun).
if os.environ.get("EMAIL_HOST"):
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.environ.get("EMAIL_HOST")
    EMAIL_PORT = int(os.environ.get("EMAIL_PORT", 587))
    EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
    EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
    EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "orders@darabistudio.pk")
STORE_OWNER_EMAIL = os.environ.get("STORE_OWNER_EMAIL", "")  # where new-order alerts go
BREVO_API_KEY = os.environ.get("BREVO_API_KEY", "")

# ---- WhatsApp order alerts (Twilio) — optional, set env vars to enable ----
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_FROM = os.environ.get("TWILIO_WHATSAPP_FROM", "")
STORE_OWNER_WHATSAPP = os.environ.get("STORE_OWNER_WHATSAPP", "")

# ---- Security hardening (auto-enabled when DEBUG=False) ----
if not DEBUG:
    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    CSRF_TRUSTED_ORIGINS = [f"https://{h}" for h in ALLOWED_HOSTS if h not in ("127.0.0.1", "localhost")]

# ---- Admin theme (Jazzmin) — branded to match the storefront ----
JAZZMIN_SETTINGS = {
    "site_title": "Darabi Studio Admin",
    "site_header": "Darabi Studio",
    "site_brand": "Darabi Studio",
    "welcome_sign": "Welcome to Darabi Studio — manage your store",
    "copyright": "Darabi Studio",
    "search_model": ["store.Product", "store.Order"],
    "show_sidebar": True,
    "navigation_expanded": True,
    "icons": {
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "store.Product": "fas fa-clock",
        "store.Category": "fas fa-tags",
        "store.Order": "fas fa-receipt",
        "store.ProductImage": "fas fa-images",
        "store.Testimonial": "fas fa-star",
    },
    "order_with_respect_to": ["store", "store.Order", "store.Product", "store.Category", "store.Testimonial", "auth"],
    "custom_css": "css/admin-theme.css",
    "show_ui_builder": False,
    "topmenu_links": [
        {"name": "Dashboard", "url": "store_dashboard", "icon": "fas fa-chart-line"},
        {"name": "Customers", "url": "store_customers", "icon": "fas fa-users"},
        {"name": "View Site", "url": "/", "new_window": True, "icon": "fas fa-store"},
    ],
}

JAZZMIN_UI_TWEAKS = {
    "navbar": "navbar-dark",
    "navbar_fixed": True,
    "theme": "darkly",
    "default_theme_mode": "dark",
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-primary",
    "brand_colour": "navbar-dark",
    "accent": "accent-warning",
    "button_classes": {
        "primary": "btn-warning",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success",
    },
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'root': {
        'handlers': ['console'],
        'level': 'ERROR',
    },
}

FILE_UPLOAD_PERMISSIONS = 0o644
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o755
