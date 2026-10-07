from django.http import HttpResponse
from flota.models import UsuarioModel

def crear_admin_temporal(request):
    correo = 'administrador@empresa.com'
    if not UsuarioModel.objects.filter(correo=correo).exists():
        UsuarioModel.objects.create_superuser(
            correo=correo,
            password='alvolante2026'
        )
        return HttpResponse("¡Usuario administrador creado con éxito! Ya puedes iniciar sesión.")
    return HttpResponse("El usuario administrador ya existía en la base de datos.")
