"""
Configuración de Django para alVolante (Proy-2026-001).
Arquitectura cliente-servidor en tres capas con patrón MVT.
Integración con PostgreSQL 16 para la persistencia de datos.
"""
import os
from pathlib import Path
import dj_database_url
BASE_DIR = Path(__file__).resolve().parent.parent
# --- Seguridad -------------------------------------------------------------
# Se lee de la variable de entorno en producción (Render) con un respaldo seguro para desarrollo local.
SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-alvolante-mvp-2026-cambiar-en-produccion")
DEBUG = os.environ.get("DEBUG", "True") == "True"
ALLOWED_HOSTS = ["*"]
# --- Aplicaciones ----------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.staticfiles",
    "django.contrib.messages",
    "flota.apps.FlotaConfig",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
# --- Plantillas ------------------------------------------------------------

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.messages.context_processors.messages",
                "flota.context_processors.usuario_actual",
            ],
        },
    },
]
# --- Persistencia (PostgreSQL) ---------------------------------------------
# dj-database-url detectará automáticamente la variable DATABASE_URL en Render.
# Si no existe (estás en local), usará la base de Render configurada por defecto.
DATABASES = {
    "default": dj_database_url.config(
        default="postgresql://alvolante_user:xYVpr4Onw6SwO1kvftrfHgcwrGYyqAwj@dpg-db3ae3bbc2fs73d4hp30-a.oregon-postgres.render.com/alvolante_db",
        conn_max_age=600,
        conn_health_checks=True,
    )
}
# Sesión y mensajes en cookie firmada, para no requerir tabla de sesiones.
SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"
SESSION_COOKIE_HTTPONLY = True
SESSION_SAVE_EVERY_REQUEST = True
MESSAGE_STORAGE = "django.contrib.messages.storage.cookie.CookieStorage"
# --- Regionalización -------------------------------------------------------
LANGUAGE_CODE = "es-co"

TIME_ZONE = "America/Bogota"
USE_I18N = True
USE_TZ = True
# --- Archivos estáticos y multimedia ----------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
# Configuración para archivos subidos por el usuario (Avatares, etc.)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
# --- Correo (HU11) ---------------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = "alertas@alvolante.com"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"