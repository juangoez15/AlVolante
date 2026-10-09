"""Casos de uso de mantenimiento preventivo (HU9, HU10)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from flota.constants import EstadoMantenimiento
from flota.domain import rules
from flota.domain.entities import Mantenimiento, Vehiculo
from flota.repositories import orm as memory


class MantenimientoNoEncontrado(Exception):
    """El mantenimiento no existe o no pertenece al vehículo indicado."""


@dataclass(frozen=True, slots=True)
class MantenimientoListado:
    """Mantenimiento con su estado calculado, listo para la plantilla."""

    mantenimiento: Mantenimiento
    estado: EstadoMantenimiento
    proximo_a_vencer: bool

    @property
    def esta_atrasado(self) -> bool:
        return self.estado is EstadoMantenimiento.ATRASADO


def obtener(mantenimiento_id: int, vehiculo_id: int) -> Mantenimiento:
    mantenimiento = memory.mantenimientos.obtener(mantenimiento_id, vehiculo_id)
    if mantenimiento is None:
        raise MantenimientoNoEncontrado(mantenimiento_id)
    return mantenimiento


def pendientes(vehiculo: Vehiculo, hoy: date | None = None) -> list[MantenimientoListado]:
    """Mantenimientos por cumplir, con estado y bandera de proximidad."""
    config = memory.configuracion.obtener()
    return [
        MantenimientoListado(
            mantenimiento=m,
            estado=rules.estado_mantenimiento(m, vehiculo.kilometraje_actual, hoy),
            proximo_a_vencer=rules.es_proximo_a_vencer(
                m, vehiculo.kilometraje_actual, config, hoy
            ),
        )
        for m in memory.mantenimientos.listar(vehiculo.id, cumplidos=False)
    ]


def historial(vehiculo: Vehiculo) -> list[Mantenimiento]:
    """Mantenimientos ya cumplidos (HU10)."""
    return memory.mantenimientos.listar(vehiculo.id, cumplidos=True)


def programar(vehiculo: Vehiculo, datos: dict[str, Any]) -> Mantenimiento:
    """Registra un mantenimiento con un único criterio: fecha o kilometraje."""
    return memory.mantenimientos.agregar(
        Mantenimiento(
            id=0,
            vehiculo_id=vehiculo.id,
            tipo=datos["tipo"],
            criterio=datos["criterio"],
            fecha_programada=datos.get("fecha_programada"),
            kilometraje_objetivo=datos.get("kilometraje_objetivo"),
        )
    )


def marcar_cumplido(mantenimiento: Mantenimiento, vehiculo: Vehiculo) -> bool:
    """
    Cierra el mantenimiento con la fecha y el kilometraje del momento (HU10).

    Devuelve False si ya estaba cumplido; el cierre es irreversible.
    """
    if mantenimiento.cumplido:
        return False
    mantenimiento.cumplido = True
    mantenimiento.fecha_cumplimiento = date.today()
    mantenimiento.kilometraje_cumplimiento = vehiculo.kilometraje_actual
    memory.mantenimientos.guardar(mantenimiento)
    return True
