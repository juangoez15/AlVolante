"""Vista del panel del administrador (HU12)."""

from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from flota.decorators import login_requerido
from flota.services import panel as servicio


@login_requerido
def panel(request: HttpRequest) -> HttpResponse:
    """Pantalla de aterrizaje con indicadores y vehículos en alerta."""
    resumen = servicio.construir_resumen(request.usuario.id)
    return render(request, "flota/panel.html", {"resumen": resumen})
