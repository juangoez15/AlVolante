from django.core.management.base import BaseCommand
from flota.models import UsuarioModel

class Command(BaseCommand):
    help = 'Crea un usuario administrador inicial automáticamente'

    def handle(self, *args, **options):
        correo = 'administrador@empresa.com'
        password = 'alvolante2026'
        
        if not UsuarioModel.objects.filter(correo=correo).exists():
            # Creamos la instancia del usuario de forma directa
            user = UsuarioModel(correo=correo)
            user.set_password(password)
            
            # Intentamos activar los permisos de superusuario según los campos que tenga el modelo
            if hasattr(user, 'is_staff'):
                user.is_staff = True
            if hasattr(user, 'is_superuser'):
                user.is_superuser = True
            if hasattr(user, 'is_active'):
                user.is_active = True
            
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Usuario administrador {correo} creado exitosamente'))
        else:
            self.stdout.write(self.style.WARNING(f'El usuario {correo} ya existe'))