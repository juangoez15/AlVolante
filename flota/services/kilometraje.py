"""Casos de uso de registro de kilometraje (HU14)."""

from __future__ import annotations

from datetime import date

from flota.constants import LECTURAS_VISIBLES
from flota.domain.entities import LecturaKilometraje, Vehiculo
from flota.repositories.orm import lecturas, vehiculos


def kilometraje_de_referencia(vehiculo: Vehiculo) -> int:
    """Último valor registrado; ninguna lectura nueva puede ser menor."""
    ultima = lecturas.ultima(vehiculo.id)
    return ultima.kilometraje if ultima else vehiculo.kilometraje_actual


def ultimas_lecturas(vehiculo: Vehiculo) -> list[LecturaKilometraje]:
    """Lecturas recientes mostradas en el detalle del vehículo (HU15)."""
    return lecturas.historico(vehiculo.id)[:LECTURAS_VISIBLES]


def registrar(vehiculo: Vehiculo, kilometraje: int, fecha_lectura: date) -> LecturaKilometraje:
    """
    Guarda la lectura y sincroniza el vehículo.

    Al actualizar el kilometraje se reevalúan automáticamente los
    mantenimientos programados por kilometraje, que pueden pasar a 'Atrasado'.
    """
    lectura = lecturas.agregar(vehiculo.id, kilometraje, fecha_lectura)
    vehiculo.kilometraje_actual = kilometraje
    vehiculo.fecha_ultima_lectura = fecha_lectura
    vehiculos.actualizar(vehiculo)  # <--- ¡Importante para guardar en PostgreSQL!
    return lectura
