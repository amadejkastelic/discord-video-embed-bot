import datetime
import json
import os
from collections import defaultdict
from pathlib import Path

import structlog

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-dftv*rt$z^!tv%y(%xs*@npo+a3svmck)rnso&g90f%ikhnu-d'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_structlog',
    'rest_framework',
    'rest_framework_simplejwt',
    'bot',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_structlog.middlewares.RequestMiddleware',
]

ROOT_URLCONF = 'bot.api.urls'

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

WSGI_APPLICATION = 'wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': os.environ.get('DJANGO_DB_ENGINE', 'django.db.backends.dummy'),
        'NAME': os.environ.get('DJANGO_DB_NAME', ''),
        'USER': os.environ.get('DJANGO_DB_USER', ''),
        'PASSWORD': os.environ.get('DJANGO_DB_PASSWORD', ''),
        'HOST': os.environ.get('DJANGO_DB_HOST', 'localhost'),
        'PORT': os.environ.get('DJANGO_DB_PORT', '5432'),
    }
}


# Caches
# https://docs.djangoproject.com/en/5.0/ref/settings/#caches

CACHES = {
    'default': {
        'BACKEND': os.environ.get('DJANGO_CACHE_BACKEND', 'django.core.cache.backends.dummy.DummyCache'),
        'LOCATION': os.environ.get('DJANGO_CACHE_LOCATION', '127.0.0.1:11211'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = False


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Logging

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'plain_console': {
            '()': structlog.stdlib.ProcessorFormatter,
            'processor': structlog.dev.ConsoleRenderer(),
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'plain_console',
        },
    },
    'loggers': {
        'django_structlog': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        # Make sure to replace the following logger's name for yours
        'bot': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.processors.TimeStamper(fmt='iso'),
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

# Rest Framework
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.IsAuthenticated',),
    'DEFAULT_AUTHENTICATION_CLASSES': ('rest_framework_simplejwt.authentication.JWTAuthentication',),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': datetime.timedelta(minutes=60),
    'SLIDING_TOKEN_REFRESH_LIFETIME': datetime.timedelta(days=1),
    'SLIDING_TOKEN_LIFETIME': datetime.timedelta(days=30),
    'SLIDING_TOKEN_REFRESH_LIFETIME_LATE_USER': datetime.timedelta(days=1),
    'SLIDING_TOKEN_LIFETIME_LATE_USER': datetime.timedelta(days=30),
}

AUTH_USER_MODEL = 'bot.User'


##########################
#       APP CONFIG       #
##########################

BOT_CONFIGURATION = {
    'discord': {
        'enabled': True,
        'api_token': os.environ.get('DISCORD_API_TOKEN', None),
    },
}

INTEGRATION_CONFIGURATION = defaultdict({}, json.loads(os.environ.get('INTEGRATION_CONFIGURATION_JSON', '{}')))

# Support secrets from environment variables for sensitive data
if 'REDDIT_CLIENT_ID' in os.environ:
    INTEGRATION_CONFIGURATION['reddit']['client_id'] = os.environ['REDDIT_CLIENT_ID']
if 'REDDIT_CLIENT_SECRET' in os.environ:
    INTEGRATION_CONFIGURATION['reddit']['client_secret'] = os.environ['REDDIT_CLIENT_SECRET']
if 'INSTAGRAM_USERNAME' in os.environ:
    INTEGRATION_CONFIGURATION['instagram']['username'] = os.environ['INSTAGRAM_USERNAME']
if 'INSTAGRAM_PASSWORD' in os.environ:
    INTEGRATION_CONFIGURATION['instagram']['password'] = os.environ['INSTAGRAM_PASSWORD']
if 'TWITTER_USERNAME' in os.environ:
    INTEGRATION_CONFIGURATION['twitter']['username'] = os.environ['TWITTER_USERNAME']
if 'TWITTER_EMAIL' in os.environ:
    INTEGRATION_CONFIGURATION['twitter']['email'] = os.environ['TWITTER_EMAIL']
if 'TWITTER_PASSWORD' in os.environ:
    INTEGRATION_CONFIGURATION['twitter']['password'] = os.environ['TWITTER_PASSWORD']
if 'BLUESKY_USERNAME' in os.environ:
    INTEGRATION_CONFIGURATION['bluesky']['username'] = os.environ['BLUESKY_USERNAME']
if 'BLUESKY_PASSWORD' in os.environ:
    INTEGRATION_CONFIGURATION['bluesky']['password'] = os.environ['BLUESKY_PASSWORD']
if 'TRUTH_SOCIAL_USERNAME' in os.environ:
    INTEGRATION_CONFIGURATION['truth_social']['username'] = os.environ['TRUTH_SOCIAL_USERNAME']
if 'TRUTH_SOCIAL_PASSWORD' in os.environ:
    INTEGRATION_CONFIGURATION['truth_social']['password'] = os.environ['TRUTH_SOCIAL_PASSWORD']

OAUTH2_CONFIGURATION = {
    'discord': {
        'client_id': None,
        'client_secret': None,
        'redirect_uri': None,
        'api_token': BOT_CONFIGURATION['discord']['api_token'],
    },
}
