"""Vista de registro manual de kilometraje (HU14)."""

from __future__ import annotations

from datetime import date

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from flota.constants import Mensajes
from flota.decorators import login_requerido
from flota.forms import KilometrajeForm
from flota.repositories.orm import vehiculos as vehiculos_orm
from flota.services import kilometraje as servicio_kilometraje


@login_requerido
def registrar(request: HttpRequest) -> HttpResponse:
    """
    Registra una lectura del odómetro.

    Admite `?vehiculo=<id>` para llegar preseleccionado desde el detalle y
    mostrar la última lectura como referencia.
    """
    vehiculos = vehiculos_orm.listar(request.usuario.id)
    seleccionado = request.GET.get("vehiculo", "")

    inicial = {"fecha_lectura": date.today()}
    if seleccionado:
        inicial["vehiculo_id"] = seleccionado

    formulario = KilometrajeForm(request.POST or None, initial=inicial, vehiculos=vehiculos)

    if request.method == "POST" and formulario.is_valid():
        vehiculo = formulario.vehiculo
        
        # Uso correcto del servicio con alias para evitar conflictos
        servicio_kilometraje.registrar(
            vehiculo,
            formulario.cleaned_data["kilometraje"],
            formulario.cleaned_data["fecha_lectura"],
        )
        
        messages.success(request, Mensajes.KILOMETRAJE_REGISTRADO)
        return redirect("vehiculo_detalle", vehiculo_id=vehiculo.id)

    contexto = {
        "form": formulario,
        "vehiculo_referencia": next(
            (v for v in vehiculos if str(v.id) == seleccionado), None
        ),
    }
    return render(request, "flota/kilometraje.html", contexto)