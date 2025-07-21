from pathlib import Path
import os
from dotenv import load_dotenv

# Charger les variables depuis le fichier .env
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY =os.getenv("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'realtime',  # L'application que tu viens de créer
    'channels',
    'rest_framework_simplejwt',  
    'rest_framework_simplejwt.token_blacklist', 
    'utilisateurs',
    'capteurs',
]

ASGI_APPLICATION = 'stageProject.asgi.application'  # Remplace 'ton_projet' par le nom de ton projet

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],  # Adresse de Redis
        },
    },
}


#Pour redis en ligne

'''CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [os.environ.get("REDIS_URL")],
            # Si Upstash nécessite TLS, ajoute aussi:
            "symmetric_encryption_keys": [os.environ.get("REDIS_ENCRYPTION_KEY", "")],  # facultatif
        },
    },
}'''


REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
}

from datetime import timedelta


SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15), #  Durée du token d'accès (très courte ici, utile pour tests)
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),    #  Durée de validité du refresh token (7 jours)
    'ROTATE_REFRESH_TOKENS': True,                  #  Active la rotation automatique des refresh tokens
    'BLACKLIST_AFTER_ROTATION': True,               #  Blackliste l’ancien refresh token après rotation
    'ALGORITHM': 'HS256',                           #  Algorithme utilisé pour signer les tokens
    'SIGNING_KEY': SECRET_KEY,                      #  Utilise la clé secrète du projet pour signer les JWT
}



AUTH_USER_MODEL="utilisateurs.User"


MIDDLEWARE = [
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# settings.py
#MY_GLOBAL_VARIABLE = "stageproject.onrender.com"
MY_GLOBAL_VARIABLE = "sc3nasi5378.universe.wf"


CSRF_TRUSTED_ORIGINS = [
    f"https://{MY_GLOBAL_VARIABLE}",  # <- ici c'est correct
]



# settings.py


ROOT_URLCONF = 'stageProject.urls'



# Chemin absolu vers le répertoire où les fichiers sont stockés
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# URL de base pour accéder aux fichiers médias
MEDIA_URL = '/media/'


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "stageProject/templates"],  # Vérifiez ce chemin
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                               # Ajoute ton context processor personnalisé ici
                'capteurs.variables.global_variables',  # Remplace 'capteur' par le nom exact de ton app
            ],
        },
    },
]







# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases



'''
import dj_database_url



DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL'),
        conn_max_age=600
    )
}'''

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
    }
}




# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'  # Chemin où collectstatic va collecter les fichiers statiques

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'


STATICFILES_DIRS = [
    BASE_DIR / 'stageProject/static',  # Static du projet principal
    BASE_DIR / 'utilisateurs/static',  # Static de l'application utilisateurs
    BASE_DIR / 'capteurs/static',  # Static de l'application capteurs
]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/



# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

#LOGIN_URL = '/utilisateurs/connexion/'  # Vérifie que ce chemin est correct
#LOGIN_REDIRECT_URL = '/utilisateurs/creer'  # Assure-toi que la page d'accueil ne redirige pas ailleurs



EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')  # Chargé depuis .env
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')  # Chargé depuis .env
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER



# settings.py
LOGIN_URL = '/login/'  # Utilise votre propre URL de connexion ici
LOGIN_REDIRECT_URL =  '/Statistique/'
LANGUAGE_CODE = 'fr'
USE_I18N = True
USE_L10N = True
USE_TZ = True

LOCALE_PATHS = [
    BASE_DIR / "locale",  # ou le chemin exact si différent
]

from django.utils.translation import gettext_lazy as _
LANGUAGES = [
    ('fr', _('Français')),
    ('en', _('English')),
    ('ar', _('العربية')),
    ('es', _('Español')),
]

