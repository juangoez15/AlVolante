"""Casos de uso sobre vehículos (HU3 a HU6, HU7, HU15) usando PostgreSQL ORM."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from flota.constants import EstadoDocumento
from flota.domain import rules
from flota.domain.entities import Vehiculo
from flota.repositories.orm import configuracion, lecturas, vehiculos


class VehiculoNoEncontrado(Exception):
    """El vehículo no existe o pertenece a otra flota."""


@dataclass(frozen=True, slots=True)
class VehiculoListado:
    """Vehículo con su estado documental, listo para la tabla de HU4."""

    vehiculo: Vehiculo
    estado: EstadoDocumento


def obtener(vehiculo_id: int, usuario_id: int) -> Vehiculo:
    """Devuelve el vehículo o lanza `VehiculoNoEncontrado` si es de otra flota."""
    vehiculo = vehiculos.obtener(vehiculo_id, usuario_id)
    if vehiculo is None:
        raise VehiculoNoEncontrado(vehiculo_id)
    return vehiculo


def listar(usuario_id: int, buscar: str = "") -> list[VehiculoListado]:
    config = configuracion.obtener()
    return [
        VehiculoListado(vehiculo, rules.estado_documental(vehiculo, config))
        for vehiculo in vehiculos.listar(usuario_id, placa_contiene=buscar)
    ]


def registrar(usuario_id: int, datos: dict[str, Any]) -> Vehiculo:
    """
    Crea el vehículo en la base de datos y su primera lectura de kilometraje (HU3).
    """
    hoy = date.today()
    vehiculo = vehiculos.agregar(
        Vehiculo(
            id=0,
            usuario_id=usuario_id,
            placa=datos["placa"],
            tipo=datos["tipo"],
            marca=datos["marca"],
            modelo=datos["modelo"],
            anio=datos["anio"],
            kilometraje_actual=datos["kilometraje_actual"],
            fecha_ultima_lectura=hoy,
        )
    )
    lecturas.agregar(vehiculo.id, vehiculo.kilometraje_actual, hoy)
    return vehiculo


def actualizar(vehiculo: Vehiculo, datos: dict[str, Any]) -> Vehiculo:
    """Actualiza los datos editables del vehículo en la BD (HU5)."""
    vehiculo.placa = datos["placa"]
    vehiculo.tipo = datos["tipo"]
    vehiculo.marca = datos["marca"]
    vehiculo.modelo = datos["modelo"]
    vehiculo.anio = datos["anio"]
    vehiculo.kilometraje_actual = datos["kilometraje_actual"]
    return vehiculos.actualizar(vehiculo)


def dar_de_baja(vehiculo: Vehiculo) -> bool:
    """Baja lógica que conserva documentos e historial (HU6)."""
    vehiculo.dar_de_baja()
    return vehiculos.actualizar(vehiculo) is not None


def actualizar_documentos(
    vehiculo: Vehiculo, vencimiento_soat: date, vencimiento_tecnomecanica: date
) -> Vehiculo:
    """Registra las fechas de SOAT y Tecnomecánica en la BD (HU7)."""
    vehiculo.vencimiento_soat = vencimiento_soat
    vehiculo.vencimiento_tecnomecanica = vencimiento_tecnomecanica
    return vehiculos.actualizar(vehiculo)


def datos_editables(vehiculo: Vehiculo) -> dict[str, Any]:
    """Valores iniciales del formulario de edición (HU5)."""
    return {
        "placa": vehiculo.placa,
        "tipo": vehiculo.tipo,
        "marca": vehiculo.marca,
        "modelo": vehiculo.modelo,
        "anio": vehiculo.anio,
        "kilometraje_actual": vehiculo.kilometraje_actual,
    }