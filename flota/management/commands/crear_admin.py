from django.core.management.base import BaseCommand
from flota.models import UsuarioModel

class Command(BaseCommand):
    help = 'Crea un usuario administrador inicial automáticamente'

    def handle(self, *args, **options):
        correo = 'administrador@empresa.com'
        if not UsuarioModel.objects.filter(correo=correo).exists():
            UsuarioModel.objects.create_superuser(
                correo=correo,
                password='alvolante2026'
            )
            self.stdout.write(self.style.SUCCESS('Usuario administrador creado exitosamente'))
        else:
            self.stdout.write('El usuario administrador ya existe')