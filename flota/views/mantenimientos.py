"""Vistas de mantenimiento preventivo (HU9, HU10)."""

from __future__ import annotations

from django.contrib import messages
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from flota.constants import Mensajes
from flota.decorators import bloquear_si_inactivo, login_requerido, traducir_no_encontrado
from flota.forms import MantenimientoForm
from flota.services import mantenimientos as servicio
from flota.services import vehiculos as servicio_vehiculos
from flota.services.mantenimientos import MantenimientoNoEncontrado


@login_requerido
@traducir_no_encontrado
def programar(request: HttpRequest, vehiculo_id: int) -> HttpResponse:
    """Programa un mantenimiento por fecha o por kilometraje (HU9)."""
    vehiculo = servicio_vehiculos.obtener(vehiculo_id, request.usuario.id)
    if bloquear_si_inactivo(request, vehiculo):
        return redirect("vehiculo_detalle", vehiculo_id=vehiculo.id)

    formulario = MantenimientoForm(request.POST or None, vehiculo=vehiculo)
    if request.method == "POST" and formulario.is_valid():
        servicio.programar(vehiculo, formulario.cleaned_data)
        messages.success(request, Mensajes.MANTENIMIENTO_CREADO)
        return redirect("vehiculo_detalle", vehiculo_id=vehiculo.id)

    contexto = {"form": formulario, "vehiculo": vehiculo}
    return render(request, "flota/mantenimiento_form.html", contexto)


@require_POST
@login_requerido
@traducir_no_encontrado
def marcar_cumplido(request: HttpRequest, vehiculo_id: int, mantenimiento_id: int) -> HttpResponse:
    """
    Cierra el mantenimiento con fecha y kilometraje actuales (HU10).

    Solo acepta POST: es una acción que modifica el estado y no debe ejecutarse
    al navegar o recargar con un enlace.
    """
    vehiculo = servicio_vehiculos.obtener(vehiculo_id, request.usuario.id)
    if bloquear_si_inactivo(request, vehiculo):
        return redirect("vehiculo_detalle", vehiculo_id=vehiculo.id)

    try:
        mantenimiento = servicio.obtener(mantenimiento_id, vehiculo.id)
    except MantenimientoNoEncontrado as error:
        raise Http404("Mantenimiento no encontrado") from error

    if servicio.marcar_cumplido(mantenimiento, vehiculo):
        messages.success(request, Mensajes.MANTENIMIENTO_CUMPLIDO)
    else:
        messages.error(request, Mensajes.MANTENIMIENTO_YA_CUMPLIDO)

    return redirect("vehiculo_detalle", vehiculo_id=vehiculo.id)
