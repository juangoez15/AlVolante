"""Vistas de autenticación y perfil (HU1, HU2, HU13)."""

from __future__ import annotations

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from flota.auth import cerrar_sesion, iniciar_sesion, usuario_autenticado
from flota.constants import Mensajes
from flota.decorators import login_requerido
from flota.forms import LoginForm, PerfilForm
from flota.services import cuentas as servicio


def login(request: HttpRequest) -> HttpResponse:
    """Punto de entrada único al sistema (HU1)."""
    if usuario_autenticado(request):
        return redirect("panel")

    formulario = LoginForm(request.POST or None)
    if request.method == "POST" and formulario.is_valid():
        usuario = servicio.autenticar(
            formulario.cleaned_data["correo"], formulario.cleaned_data["password"]
        )
        if usuario is None:
            formulario.add_error(None, Mensajes.CREDENCIALES_INVALIDAS)
        else:
            iniciar_sesion(request, usuario)
            return redirect("panel")

    return render(request, "flota/login.html", {"form": formulario})


def logout(request: HttpRequest) -> HttpResponse:
    """Cierra la sesión y vuelve al formulario de acceso (HU2)."""
    cerrar_sesion(request)
    return redirect("login")


@login_requerido
def perfil(request: HttpRequest) -> HttpResponse:
    """Consulta y actualización de los datos del administrador (HU13)."""
    usuario = request.usuario
    inicial = {"nombre": usuario.nombre, "correo": usuario.correo}
    
    # Recogemos tanto los datos POST como los archivos FILES (la imagen)
    formulario = PerfilForm(request.POST or None, request.FILES or None, initial=inicial, usuario=usuario)

    if request.method == "POST" and formulario.is_valid():
        # Capturamos el archivo de la imagen que se subió al hacer clic en el icono
        avatar_file = request.FILES.get('avatar')

        resultado = servicio.actualizar_perfil(
            usuario,
            nombre=formulario.cleaned_data["nombre"].strip(),
            correo=formulario.cleaned_data["correo"],
            password=formulario.cleaned_data["password"],
            avatar_file=avatar_file,  # <-- Se lo pasamos al servicio aquí sin error
        )
        messages.success(request, Mensajes.PERFIL_ACTUALIZADO)

        if resultado.requiere_reautenticacion:
            cerrar_sesion(request)
            return redirect("login")
        return redirect("perfil")

    return render(request, "flota/perfil.html", {"form": formulario})
