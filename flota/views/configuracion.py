"""Vista de configuración de alertas automáticas (HU11)."""

from __future__ import annotations

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from flota.constants import Mensajes
from flota.decorators import login_requerido
from flota.forms import AlertasForm
from flota.services import configuracion as servicio


@login_requerido
def alertas(request: HttpRequest) -> HttpResponse:
    """Define umbrales de anticipación y destinatario de las notificaciones."""
    formulario = AlertasForm(request.POST or None, initial=servicio.datos_editables())

    if request.method == "POST" and formulario.is_valid():
        servicio.guardar(
            umbrales_dias=formulario.cleaned_data["umbrales_dias"],
            umbral_km=formulario.cleaned_data["umbral_km"],
            correo_notificaciones=formulario.cleaned_data["correo_notificaciones"],
        )
        messages.success(request, Mensajes.CONFIGURACION_GUARDADA)
        return redirect("alertas")

    return render(request, "flota/alertas.html", {"form": formulario})
