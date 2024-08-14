import datetime
from pathlib import Path

import structlog

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-dftv*rt$z^!tv%y(%xs*@npo+a3svmck)rnso&g90f%ikhnu-d'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

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
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'embed_bot',
        'USER': 'bot',
        'PASSWORD': 'bot',
        'HOST': '127.0.0.1',
        'PORT': 5432,
    }
}


# Caches
# https://docs.djangoproject.com/en/5.0/ref/settings/#caches

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.PyMemcacheCache',
        'LOCATION': [
            '127.0.0.1:11211',
        ],
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
        'json_formatter': {
            '()': structlog.stdlib.ProcessorFormatter,
            'processor': structlog.processors.JSONRenderer(),
        },
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
        'json_file': {
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': 'json.log',
            'formatter': 'json_formatter',
        },
    },
    'loggers': {
        'django_structlog': {
            'handlers': ['console', 'json_file'],
            'level': 'INFO',
        },
        # Make sure to replace the following logger's name for yours
        'bot': {
            'handlers': ['console', 'json_file'],
            'level': 'INFO',
        },
    },
}

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.processors.TimeStamper(fmt="iso"),
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


##########################
#       APP CONFIG       #
##########################

BOT_CONFIGURATION = {
    'discord': {
        'enabled': False,
        'api_token': None,
    },
}

OAUTH2_CONFIGURATION = {
    'discord': {
        'client_id': None,
        'client_secret': None,
        'redirect_uri': None,
        'api_token': BOT_CONFIGURATION['discord']['api_token'],
    },
}

INTEGRATION_CONFIGURATION = {
    'tiktok': {
        'enabled': False,
    },
    'instagram': {
        'enabled': False,
        'session_file_path': None,
        'username': None,
        'user_agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/116.0',
    },
    'facebook': {
        'enabled': False,
        'cookies_file_path': None,
    },
    'reddit': {
        'enabled': False,
        'client_id': None,
        'client_secret': None,
        'user_agent': None,
    },
    'youtube': {
        'enabled': False,
    },
    'twitter': {
        'enabled': False,
        'username': None,
        'email': None,
        'password': None,
    },
    'twitch': {
        'enabled': False,
    },
}
