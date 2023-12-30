from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-jcfkm1q@7_i1)eq@2&emyb)ixr2do3ozt^ab!o^w-dbgq)ognj'

# SECURITY WARNING: don't run with debug turned on in production!
CSRF_COOKIE_SECURE = False  # Set to True if using HTTPS
CSRF_COOKIE_HTTPONLY = True


DEBUG = True
ALLOWED_HOSTS = [
    # "*",
    "34.138.81.48",
    "34.74.147.25",
    "api.boostedchat.com",
    "elth.uk.boostedchat.com",
    "127.0.0.1",
    "a69c-105-60-202-188.ngrok-free.app",
    "3e6a-62-8-92-218.ngrok-free.app",
    "3e6a-62-8-92-218.ngrok-fr",
    "api.booksy.us.boostedchat.com",
    "promptemplate.boostedchat.com",
    "promptemplate.booksy.boostedchat.com",
    "ce2d-105-161-11-162.ngrok-free.app",
    "ed48-196-105-37-1.ngrok-free.app"
    "prompt",
    "ed48-196-105-37-1.ngrok-free.app",
]

CSRF_TRUSTED_ORIGINS = [
    "https://api.boostedchat.com",
    "https://api.booksy.us.boostedchat.com",
    "https://a69c-105-60-202-188.ngrok-free.app",
    "https://3e6a-62-8-92-218.ngrok-free.app",
    "https://3e6a-62-8-92-218.ngrok-fr",
    "https://ce2d-105-161-11-162.ngrok-free.app",
    "http://promptemplate.boostedchat.com",
    "http://promptemplate.booksy.boostedchat.com",
    "https://promptemplate.booksy.boostedchat.com",
]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'softdelete',
    'product',
    'prompt',
    'helpers'
]

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ]
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'main.urls'

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

WSGI_APPLICATION = 'main.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    },
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = '/usr/src/app/static'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


USE_TZ = True
TIME_ZONE = 'UTC'  # Set to your desired time zone, e.g., 'America/New_York'
