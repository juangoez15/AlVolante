"""Consolidado de la flota para el panel del administrador (HU12)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from flota.constants import EstadoDocumento, EstadoMantenimiento
from flota.domain import rules
from flota.domain.entities import Vehiculo
from flota.repositories.orm import configuracion, vehiculos
from flota.services import mantenimientos as servicio_mantenimientos


@dataclass(frozen=True, slots=True)
class FilaAtencion:
    """Vehículo que requiere acción, con el motivo ya resuelto."""

    vehiculo: Vehiculo
    estado_soat: EstadoDocumento
    estado_tecnomecanica: EstadoDocumento
    proximo_mantenimiento: str
    tiene_mantenimiento_atrasado: bool


@dataclass(slots=True)
class ResumenFlota:
    """Indicadores superiores del panel y listado de vehículos en alerta."""

    al_dia: int = 0
    por_vencer: int = 0
    vencidos: int = 0
    sin_registro: int = 0
    atencion: list[FilaAtencion] = field(default_factory=list)

    @property
    def total(self) -> int:
        return self.al_dia + self.por_vencer + self.vencidos + self.sin_registro


#: Estados documentales que por sí solos justifican mostrar el vehículo en el panel.
_ESTADOS_EN_ALERTA = frozenset(
    {EstadoDocumento.VENCIDO, EstadoDocumento.POR_VENCER, EstadoDocumento.SIN_REGISTRO}
)


def construir_resumen(usuario_id: int, hoy: date | None = None) -> ResumenFlota:
    """Recorre la flota activa y calcula indicadores y alertas desde PostgreSQL."""
    config = configuracion.obtener()
    resumen = ResumenFlota()

    for vehiculo in vehiculos.listar(usuario_id):
        estado_documental = rules.estado_documental(vehiculo, config, hoy)
        _acumular_indicador(resumen, estado_documental)

        pendientes = servicio_mantenimientos.pendientes(vehiculo, hoy)
        hay_atrasado = any(p.esta_atrasado for p in pendientes)
        hay_proximo = any(p.proximo_a_vencer for p in pendientes)

        if estado_documental in _ESTADOS_EN_ALERTA or hay_atrasado or hay_proximo:
            resumen.atencion.append(
                FilaAtencion(
                    vehiculo=vehiculo,
                    estado_soat=rules.estado_soat(vehiculo, config, hoy),
                    estado_tecnomecanica=rules.estado_tecnomecanica(vehiculo, config, hoy),
                    proximo_mantenimiento=rules.proximo_mantenimiento(
                        [p.mantenimiento for p in pendientes], vehiculo, config, hoy
                    ),
                    tiene_mantenimiento_atrasado=hay_atrasado,
                )
            )

    return resumen


def _acumular_indicador(resumen: ResumenFlota, estado: EstadoDocumento) -> None:
    """Suma el vehículo al contador que corresponde a su estado documental."""
    match estado:
        case EstadoDocumento.VENCIDO:
            resumen.vencidos += 1
        case EstadoDocumento.POR_VENCER:
            resumen.por_vencer += 1
        case EstadoDocumento.SIN_REGISTRO:
            resumen.sin_registro += 1
        case _:
            resumen.al_dia += 1


__all__ = ["FilaAtencion", "ResumenFlota", "construir_resumen", "EstadoMantenimiento"]
