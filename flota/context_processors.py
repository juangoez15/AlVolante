"""Datos disponibles en todas las plantillas."""

from __future__ import annotations

from django.http import HttpRequest

from flota.auth import usuario_autenticado


def usuario_actual(request: HttpRequest) -> dict:
    """Expone el administrador autenticado al encabezado común."""
    return {"usuario": usuario_autenticado(request)}
