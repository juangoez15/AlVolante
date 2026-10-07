from django.core.management.base import BaseCommand
from flota.models import UsuarioModel

class Command(BaseCommand):
    help = 'Crea un usuario administrador inicial automáticamente'

    def handle(self, *args, **options):
        correo = 'administrador@empresa.com'
        password = 'alvolante2026'
        
        if not UsuarioModel.objects.filter(correo=correo).exists():
            # Creamos el usuario asignando directamente la contraseña y campos comunes
            usuario = UsuarioModel(correo=correo, password=password)
            
            # Activamos flags de permisos si existen en tu modelo
            if hasattr(usuario, 'is_staff'):
                usuario.is_staff = True
            if hasattr(usuario, 'is_superuser'):
                usuario.is_superuser = True
            if hasattr(usuario, 'is_active'):
                usuario.is_active = True
            
            usuario.save()
            self.stdout.write(self.style.SUCCESS(f'Usuario administrador {correo} creado exitosamente'))
        else:
            self.stdout.write(self.style.WARNING(f'El usuario {correo} ya existe'))