"""Decoradores transversales de las vistas."""

from __future__ import annotations

from functools import wraps
from typing import Callable

from django.contrib import messages
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect

from flota.auth import usuario_autenticado
from flota.constants import Mensajes
from flota.services.vehiculos import VehiculoNoEncontrado

Vista = Callable[..., HttpResponse]


def login_requerido(vista: Vista) -> Vista:
    """
    Exige sesión activa y expone `request.usuario` a la vista (HU2).

    Evita que cada vista repita la comprobación y garantiza que todas las
    consultas posteriores queden acotadas a la flota del usuario.
    """

    @wraps(vista)
    def _envoltura(request: HttpRequest, *args, **kwargs) -> HttpResponse:
        usuario = usuario_autenticado(request)
        if usuario is None:
            return redirect("login")
        request.usuario = usuario
        return vista(request, *args, **kwargs)

    return _envoltura


def traducir_no_encontrado(vista: Vista) -> Vista:
    """
    Convierte `VehiculoNoEncontrado` en un 404.

    Un vehículo de otra flota es indistinguible de uno inexistente, de modo que
    la respuesta no revela si el identificador existe en el sistema.
    """

    @wraps(vista)
    def _envoltura(request: HttpRequest, *args, **kwargs) -> HttpResponse:
        try:
            return vista(request, *args, **kwargs)
        except VehiculoNoEncontrado as error:
            raise Http404("Vehículo no encontrado") from error

    return _envoltura


def bloquear_si_inactivo(request: HttpRequest, vehiculo) -> bool:
    """
    Impide modificar un vehículo dado de baja (HU6).

    Se aplica en todas las vistas de escritura, no solo en la edición: sin esta
    validación bastaría entrar por URL para actualizar documentos, programar
    mantenimientos o registrar cumplimientos sobre un vehículo inactivo.
    """
    if vehiculo.activo:
        return False
    messages.error(request, Mensajes.VEHICULO_INACTIVO)
    return True
