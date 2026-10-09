"""Enrutamiento raíz del proyecto."""

from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path, re_path
from django.views.static import serve

urlpatterns = [
    path("", include("flota.urls")),
    
]

# Servir archivos multimedia (avatares). En Render DEBUG=False, por lo que
# static() no registra nada; se usa serve() de forma explícita.
urlpatterns += [
    re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
]