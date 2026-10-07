"""
Reglas de negocio de alVolante.

Funciones puras que reciben entidades y configuración y devuelven estados o
métricas. Al no tener estado propio ni dependencias de framework, son el punto
natural para las pruebas unitarias y no cambian cuando se conecte PostgreSQL.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from flota.constants import EstadoDocumento, EstadoMantenimiento
from flota.domain.entities import Configuracion, Mantenimiento, Vehiculo


def _hoy(referencia: date | None = None) -> date:
    """Permite inyectar la fecha en las pruebas sin parchear `date.today`."""
    return referencia or date.today()


# ---------------------------------------------------------------------------
# Documentos legales (HU8)
# ---------------------------------------------------------------------------


def estado_documento(
    vencimiento: date | None, config: Configuracion, hoy: date | None = None
) -> EstadoDocumento:
    """Clasifica un documento según su fecha de vencimiento."""
    hoy = _hoy(hoy)
    if vencimiento is None:
        return EstadoDocumento.SIN_REGISTRO
    if vencimiento < hoy:
        return EstadoDocumento.VENCIDO
    if (vencimiento - hoy).days <= config.umbral_mayor:
        return EstadoDocumento.POR_VENCER
    return EstadoDocumento.VIGENTE


def estado_soat(vehiculo: Vehiculo, config: Configuracion, hoy: date | None = None):
    return estado_documento(vehiculo.vencimiento_soat, config, hoy)


def estado_tecnomecanica(vehiculo: Vehiculo, config: Configuracion, hoy: date | None = None):
    return estado_documento(vehiculo.vencimiento_tecnomecanica, config, hoy)


def estado_documental(
    vehiculo: Vehiculo, config: Configuracion, hoy: date | None = None
) -> EstadoDocumento:
    """
    Estado consolidado que se muestra en el listado y el panel.

    Un vehículo recién registrado no tiene fechas (HU3 no las pide), por lo que
    se reporta como `SIN_REGISTRO` en vez de `VIGENTE`: sin fechas no se puede
    afirmar que esté al día.
    """
    estados = {estado_soat(vehiculo, config, hoy), estado_tecnomecanica(vehiculo, config, hoy)}
    for estado in (
        EstadoDocumento.VENCIDO,
        EstadoDocumento.POR_VENCER,
        EstadoDocumento.SIN_REGISTRO,
    ):
        if estado in estados:
            return estado
    return EstadoDocumento.VIGENTE


# ---------------------------------------------------------------------------
# Mantenimiento preventivo (HU9)
# ---------------------------------------------------------------------------


def estado_mantenimiento(
    mantenimiento: Mantenimiento,
    km_actual: int,
    hoy: date | None = None,
) -> EstadoMantenimiento:
    """Pendiente → Atrasado al superarse la fecha o el kilometraje objetivo."""
    hoy = _hoy(hoy)
    if mantenimiento.cumplido:
        return EstadoMantenimiento.CUMPLIDO
    if mantenimiento.es_por_fecha and mantenimiento.fecha_programada:
        if mantenimiento.fecha_programada < hoy:
            return EstadoMantenimiento.ATRASADO
    elif mantenimiento.es_por_kilometraje and mantenimiento.kilometraje_objetivo is not None:
        if km_actual >= mantenimiento.kilometraje_objetivo:
            return EstadoMantenimiento.ATRASADO
    return EstadoMantenimiento.PENDIENTE


def es_proximo_a_vencer(
    mantenimiento: Mantenimiento,
    km_actual: int,
    config: Configuracion,
    hoy: date | None = None,
) -> bool:
    """Indica si el mantenimiento entra en la ventana de alerta configurada."""
    hoy = _hoy(hoy)
    if mantenimiento.cumplido:
        return False
    if mantenimiento.es_por_fecha and mantenimiento.fecha_programada:
        return 0 <= (mantenimiento.fecha_programada - hoy).days <= config.umbral_mayor
    if mantenimiento.es_por_kilometraje and mantenimiento.kilometraje_objetivo is not None:
        return 0 <= mantenimiento.kilometraje_objetivo - km_actual <= config.umbral_km
    return False


@dataclass(frozen=True, slots=True)
class Urgencia:
    """
    Proximidad comparable de un mantenimiento.

    `atrasado` ordena primero y `proporcion` normaliza días y kilómetros contra
    su umbral respectivo. Sin esta normalización, comparar 300 km contra 20 días
    como números crudos haría que el de kilometraje siempre pareciera más lejano.
    """

    atrasado: bool
    proporcion: float
    texto: str

    @property
    def clave_orden(self) -> tuple[int, float]:
        return (0 if self.atrasado else 1, self.proporcion)


def urgencia_mantenimiento(
    mantenimiento: Mantenimiento,
    vehiculo: Vehiculo,
    config: Configuracion,
    hoy: date | None = None,
) -> Urgencia | None:
    """Traduce el criterio del mantenimiento a una urgencia comparable."""
    hoy = _hoy(hoy)

    if mantenimiento.es_por_fecha and mantenimiento.fecha_programada:
        dias = (mantenimiento.fecha_programada - hoy).days
        if dias < 0:
            return Urgencia(True, 0.0, f"Atrasado {abs(dias)} días")
        return Urgencia(False, dias / max(config.umbral_mayor, 1), f"En {dias} días")

    if mantenimiento.es_por_kilometraje and mantenimiento.kilometraje_objetivo is not None:
        restantes = mantenimiento.kilometraje_objetivo - vehiculo.kilometraje_actual
        if restantes < 0:
            texto = f"Atrasado {abs(restantes):,} km".replace(",", ".")
            return Urgencia(True, 0.0, texto)
        texto = f"En {restantes:,} km".replace(",", ".")
        return Urgencia(False, restantes / max(config.umbral_km, 1), texto)

    return None


def proximo_mantenimiento(
    mantenimientos: list[Mantenimiento],
    vehiculo: Vehiculo,
    config: Configuracion,
    hoy: date | None = None,
) -> str:
    """Texto del mantenimiento pendiente más urgente, para el panel (HU12)."""
    urgencias = [
        urgencia
        for m in mantenimientos
        if not m.cumplido
        if (urgencia := urgencia_mantenimiento(m, vehiculo, config, hoy)) is not None
    ]
    if not urgencias:
        return "Sin programar"
    return min(urgencias, key=lambda u: u.clave_orden).texto
