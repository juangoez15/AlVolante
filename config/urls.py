from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from flota.views import crear_admin_temporal  # <--- 1. Importa la vista aquí

urlpatterns = [
    path("", include("flota.urls")),
    path('crear-admin-seguro/', crear_admin_temporal),  # <--- 2. Añade la ruta aquí
]

# Servir archivos multimedia en entorno de desarrollo (DEBUG = True)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)