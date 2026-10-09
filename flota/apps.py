"""Configuración de la aplicación de gestión de flota."""

from django.apps import AppConfig


class FlotaConfig(AppConfig):
    name = "flota"
    verbose_name = "Gestión de flota"

    def ready(self) -> None:
        """Los datos viven en PostgreSQL; ya no se siembra memoria al iniciar."""
        return None
