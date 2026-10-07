"""Configuración de la aplicación de gestión de flota."""

from django.apps import AppConfig


class FlotaConfig(AppConfig):
    name = "flota"
    verbose_name = "Gestión de flota"

    def ready(self) -> None:
        """Carga los datos de demostración y asegura el usuario administrador al iniciar el proceso."""
        # 1. Cargar datos de demostración que ya tenías
        try:
            from flota.repositories.seed import cargar_datos_demo
            cargar_datos_demo()
        except Exception:
            pass

        # 2. Crear el usuario administrador automáticamente si no existe
        import sys
        if 'runserver' in sys.argv or 'gunicorn' in sys.argv:
            try:
                from flota.models import UsuarioModel
                correo = 'administrador@empresa.com'
                if not UsuarioModel.objects.filter(correo=correo).exists():
                    UsuarioModel.objects.create_superuser(
                        correo=correo,
                        password='alvolante2026'
                    )
            except Exception:
                pass