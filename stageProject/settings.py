"""
Django settings for stageProject project.

Generated by 'django-admin startproject' using Django 5.1.6.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-t(!jq=!+e$^tw_n=nhjtkj)1u%m&g4tad-u125ojcs21(n_=9r'

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
    'utilisateurs',
    'capteurs',
]

ASGI_APPLICATION = 'stageproject.asgi.application'  # Remplace 'ton_projet' par le nom de ton projet

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],  # Adresse de Redis
        },
    },
}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
}

from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),  # Durée de validité du token d'accès
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),     # Durée de validité du token de rafraîchissement
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
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
MY_GLOBAL_VARIABLE = "triple-stereo-dealtime-asylum.trycloudflare.com"

CSRF_TRUSTED_ORIGINS = [
    f"https://{MY_GLOBAL_VARIABLE}",  # <- ici c'est correct
]



# settings.py


ROOT_URLCONF = 'stageProject.urls'

import os

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



ASGI_APPLICATION = 'stageproject.asgi.application'



# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'stage_database',   # Remplacez par le nom de votre base de données
        'USER': 'migouelito',             # Remplacez par votre nom d'utilisateur PostgreSQL
        'PASSWORD': '1234',            # Remplacez par votre mot de passe
        'HOST': 'localhost',                   # Si vous utilisez PostgreSQL localement
        'PORT': '5432',                        # Le port par défaut de PostgreSQL
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


from dotenv import load_dotenv
import os

load_dotenv()  # Charge les variables d'environnement depuis .env

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')  # Chargé depuis .env
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')  # Chargé depuis .env
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER





LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'ERROR',  # Enregistre uniquement les erreurs
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'mail_errors.log'),  # Fichier log dans le projet
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
        'django.core.mail': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}

import logging

logger = logging.getLogger('django.core.mail')  # Logger pour les emails

logger.error("Test d'erreur : Ceci est un test pour voir si les logs fonctionnent bien")

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

