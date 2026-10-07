"""Configuración de la aplicación de gestión de flota."""

from django.apps import AppConfig


class FlotaConfig(AppConfig):
    name = "flota"
    verbose_name = "Gestión de flota"

    def ready(self) -> None:
        """Carga los datos de demostración al iniciar el proceso."""
        from flota.repositories.seed import cargar_datos_demo

        cargar_datos_demo()
