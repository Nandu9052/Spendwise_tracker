"""
Django settings for SpendWise - Personal Expense Tracker & Smart Budget Alerts
"""

from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-spendwise-hackathon-secret-key-2024-change-in-production'

DEBUG = True

# Accept every hostname — required for LEARNSQUARE/SemesterPrep reverse proxy
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'tracker',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'tracker.middleware.DynamicCsrfMiddleware',   # must come BEFORE CsrfViewMiddleware
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ──────────────────────────────────────────────────────────────────────────────
# PROXY / REVERSE-PROXY SETTINGS
# Required for LEARNSQUARE, SemesterPrep, Gitpod, Codespaces, Coder, etc.
# ──────────────────────────────────────────────────────────────────────────────
#
# Tell Django to trust the X-Forwarded-Proto header so it knows the request
# arrived over HTTPS even though Django itself speaks HTTP internally.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# NEVER set SECURE_SSL_REDIRECT = True in a reverse-proxy environment.
# That causes infinite redirect loops because Django sees HTTP internally
# while the proxy reports HTTPS externally.
SECURE_SSL_REDIRECT = False

# Seed list — DynamicCsrfMiddleware will append the live request host at
# runtime, so forms work on any proxy hostname automatically.
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'http://0.0.0.0:8000',
    'https://localhost:8000',
    'https://127.0.0.1:8000',
]

# Session cookies: let the browser decide (works on both HTTP and HTTPS)
SESSION_COOKIE_SECURE = False   # False = works on HTTP too; proxy handles HTTPS
CSRF_COOKIE_SECURE = False      # same reason

# Prevent X-Frame-Options from blocking the workspace preview iframe (if any)
X_FRAME_OPTIONS = 'SAMEORIGIN'

ROOT_URLCONF = 'spendwise.urls'

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

WSGI_APPLICATION = 'spendwise.wsgi.application'

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
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = []

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ──────────────────────────────────────────────────────────────────────────────
# Authentication URLs
# ──────────────────────────────────────────────────────────────────────────────
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/login/'

# Messages
from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.DEBUG: 'secondary',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}
