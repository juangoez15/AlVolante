from django.apps import AppConfig

class FlotaConfig(AppConfig):
    name = "flota"
    verbose_name = "Gestión de flota"

    def ready(self) -> None:
        try:
            from flota.repositories.seed import cargar_datos_demo
            cargar_datos_demo()
        except Exception:
            pass

        import sys
        if 'gunicorn' in sys.argv:
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