"""Filtros de presentación usados en las plantillas."""

from __future__ import annotations

from django import template

from flota.constants import EstadoDocumento, EstadoMantenimiento

register = template.Library()

#: Traducción de cada estado a la clase CSS del chip correspondiente.
_CLASES_ESTADO = {
    EstadoDocumento.VIGENTE: "badge-ok",
    EstadoDocumento.POR_VENCER: "badge-warn",
    EstadoDocumento.VENCIDO: "badge-danger",
    EstadoDocumento.SIN_REGISTRO: "badge-neutral",
    EstadoMantenimiento.CUMPLIDO: "badge-ok",
    EstadoMantenimiento.PENDIENTE: "badge-warn",
    EstadoMantenimiento.ATRASADO: "badge-danger",
}

SIN_DATO = "—"


@register.filter
def badge(estado) -> str:
    """Clase CSS del chip de estado; neutra si el valor no se reconoce."""
    return _CLASES_ESTADO.get(estado, "badge-neutral")


@register.filter
def km(valor) -> str:
    """
    Formatea kilometraje con separador de miles.

    Devuelve un guion cuando no hay dato, para no imprimir "None km" en
    mantenimientos cumplidos sin kilometraje asociado.
    """
    if valor is None or valor == "":
        return SIN_DATO
    try:
        return f"{int(valor):,}".replace(",", ".")
    except (TypeError, ValueError):
        return str(valor)
