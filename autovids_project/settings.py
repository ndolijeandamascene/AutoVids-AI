"""
Django settings for AutoVids AI - AI-Powered Video Automation Platform
"""

from pathlib import Path
import environ
import os

# Initialize environment variables
env = environ.Env(
    DEBUG=(bool, True),
    ALLOWED_HOSTS=(list, []),
)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Read .env file if it exists
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY', default='django-insecure-x$z^64gz&$=jp*ky$7qti-f0pczr*uk5b5kuo^()4xi)-d^j%i')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG')

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party apps
    'django_celery_beat',
    
    # Custom apps
    'content',
    'media_engine',
    'automation',
    'accounts',
    'analytics',
    'dashboard',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'autovids_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
            ],
        },
    },
]

WSGI_APPLICATION = 'autovids_project.wsgi.application'


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# For production, use PostgreSQL:
# DATABASES = {
#     'default': env.db('DATABASE_URL')
# }


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Media files (User uploads, generated videos)
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ============================================================================
# CELERY CONFIGURATION
# ============================================================================

CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Celery Beat Schedule
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'generate-daily-content': {
        'task': 'automation.tasks.generate_daily_content',
        'schedule': crontab(hour=8, minute=0),  # 8 AM daily
    },
    'schedule-daily-uploads': {
        'task': 'automation.tasks.schedule_daily_uploads',
        'schedule': crontab(hour=9, minute=0),  # 9 AM daily
    },
    'process-scheduled-uploads': {
        'task': 'automation.tasks.process_scheduled_uploads',
        'schedule': crontab(minute='*/15'),  # Every 15 minutes
    },
    'sync-video-analytics': {
        'task': 'automation.tasks.sync_video_analytics',
        'schedule': crontab(hour='*/6'),  # Every 6 hours
    },
    'cleanup-old-files': {
        'task': 'automation.tasks.cleanup_old_files',
        'schedule': crontab(hour=2, minute=0),  # 2 AM daily
    },
}


# ============================================================================
# AI API KEYS
# ============================================================================

OPENAI_API_KEY = env('OPENAI_API_KEY', default='')
ANTHROPIC_API_KEY = env('ANTHROPIC_API_KEY', default='')
GOOGLE_AI_API_KEY = env('GOOGLE_AI_API_KEY', default='')

# ElevenLabs TTS
ELEVENLABS_API_KEY = env('ELEVENLABS_API_KEY', default='')


# ============================================================================
# CONTENT GENERATION SETTINGS
# ============================================================================

DEFAULT_AI_PROVIDER = env('DEFAULT_AI_PROVIDER', default='openai')
DEFAULT_TTS_PROVIDER = env('DEFAULT_TTS_PROVIDER', default='elevenlabs')

# Upload limits
MAX_VIDEOS_PER_DAY = env.int('MAX_VIDEOS_PER_DAY', default=2)
MIN_HOURS_BETWEEN_POSTS = env.int('MIN_HOURS_BETWEEN_POSTS', default=8)


# ============================================================================
# SAFETY & AUTOMATION SETTINGS
# ============================================================================

ACCOUNT_AGE_DAYS_BEFORE_AUTO = env.int('ACCOUNT_AGE_DAYS_BEFORE_AUTO', default=7)
ENABLE_HUMAN_BEHAVIOR = env.bool('ENABLE_HUMAN_BEHAVIOR', default=True)
RANDOM_DELAY_MIN_SECONDS = env.int('RANDOM_DELAY_MIN_SECONDS', default=30)
RANDOM_DELAY_MAX_SECONDS = env.int('RANDOM_DELAY_MAX_SECONDS', default=180)


# ============================================================================
# LOGGING
# ============================================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'autovids.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'content': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'automation': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
