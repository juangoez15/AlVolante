"""Casos de uso de la configuración de alertas (HU11)."""

from __future__ import annotations

from flota.domain.entities import Configuracion
from flota.repositories import memory


def obtener() -> Configuracion:
    return memory.configuracion.obtener()


def datos_editables() -> dict:
    """Valores iniciales del formulario de alertas."""
    config = obtener()
    return {
        "umbrales_dias": [str(dia) for dia in config.umbrales_dias],
        "umbral_km": config.umbral_km,
        "correo_notificaciones": config.correo_notificaciones,
    }


def guardar(umbrales_dias: list[int], umbral_km: int, correo_notificaciones: str) -> Configuracion:
    return memory.configuracion.guardar(
        umbrales_dias=umbrales_dias,
        umbral_km=umbral_km,
        correo_notificaciones=correo_notificaciones,
    )
