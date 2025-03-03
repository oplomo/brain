from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-!kdbpe1)1l+3pqg@y!w)m^n#o32*j0#b(qhmg7izz-2%0iz6m^"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True


ALLOWED_HOSTS = ["www.jeruscore.com", "jeruscore.com", "brain-zofx.onrender.com"]
INSTALLED_APPS = [
    "django.contrib.sitemaps",
    "django.contrib.sites",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "square.apps.SquareConfig",
    "backend.apps.BackendConfig",
    "django_celery_beat",
]

SITE_ID = 2


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

MIDDLEWARE.append("square.middleware.MaintenanceMiddleware")

MAINTENANCE_MODE = False

ROOT_URLCONF = "brain.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "square.context_processors.site_info_context",
            ],
        },
    },
]

WSGI_APPLICATION = "brain.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.sqlite3",
#         "NAME": BASE_DIR / "db.sqlite3",
#     }
# }

import os
import dj_database_url

DATABASES = {"default": dj_database_url.config(default=os.getenv("DATABASE_URL"))}


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 4},
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"  # Django will collect files here
STATICFILES_DIRS = []
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

import os

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# import os
# import dj_database_url

# DATABASES = {"default": dj_database_url.config(default=os.getenv("DATABASE_URL"))}

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

X_FRAME_OPTIONS = "SAMEORIGIN"

TIME_ZONE = "UTC"
USE_TZ = True


import os
from kombu import Connection

CELERY_BROKER_URL = "rediss://default:AZuCAAIjcDFjZjAxN2U3MzdjNzA0MGI0YjBlNzRmOTAzODM1N2NkMHAxMA@enabling-halibut-39810.upstash.io:6379?ssl_cert_reqs=optional"
CELERY_RESULT_BACKEND = "rediss://default:AZuCAAIjcDFjZjAxN2U3MzdjNzA0MGI0YjBlNzRmOTAzODM1N2NkMHAxMA@enabling-halibut-39810.upstash.io:6379?ssl_cert_reqs=optional"

CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"
CELERY_WORKER_CONCURRENCY = 4
# rediss://default:AZuCAAIjcDFjZjAxN2U3MzdjNzA0MGI0YjBlNzRmOTAzODM1N2NkMHAxMA@enabling-halibut-39810.upstash.io:6379?ssl_cert_reqs=optional
# REDIS_URL
# DATABASE_URL
# postgresql://predict_db_user:USygJJYAf1u1rP8XVuvqfmSPFKVnkGWg@dpg-cv2b7h8gph6c73bem560-a/predict_db
CELERY_BROKER_TRANSPORT_OPTIONS = {
    "visibility_timeout": 3600,
    "ssl": {
        "ssl_cert_reqs": "CERT_NONE"  # Change to "CERT_REQUIRED" if you have a valid certificate
    },
}

# settings.py
PAYSTACK_PUBLIC_KEY = "YOUR_PUBLIC_KEY"
PAYSTACK_SECRET_KEY = "sk_test_72090b3352c0b135db0d7a96cb4977418ccbb1d5"
PAYSTACK_CALLBACK_URL = "http://127.0.0.1:8000/payment/callback/"
