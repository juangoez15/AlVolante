from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from flota.constants import (
    UMBRAL_DIAS_DEFECTO,
    UMBRAL_KM_DEFECTO,
    CriterioMantenimiento,
    TipoVehiculo,
)


@dataclass(slots=True)
class Usuario:
    """Administrador de flota. Las cuentas las crea el equipo de alVolante (HU1)."""

    id: int
    nombre: str
    correo: str
    password: str
    avatar: str | None = None  # <-- Añadido


@dataclass(slots=True)
class Configuracion:
    """Preferencias de las alertas automáticas de vencimiento (HU11)."""

    umbrales_dias: list[int] = field(
        default_factory=lambda: list(UMBRAL_DIAS_DEFECTO for _ in range(1))
    )
    umbral_km: int = UMBRAL_KM_DEFECTO
    correo_notificaciones: str = "administrador@empresa.com"

    @property
    def umbral_mayor(self) -> int:
        """Ventana de anticipación más amplia; define qué es 'próximo a vencer'."""
        return max(self.umbrales_dias) if self.umbrales_dias else UMBRAL_DIAS_DEFECTO


@dataclass(slots=True)
class LecturaKilometraje:
    """Lectura puntual del odómetro, registrada manualmente (HU14)."""

    id: int
    vehiculo_id: int
    kilometraje: int
    fecha_lectura: date


@dataclass(slots=True)
class Mantenimiento:
    """Mantenimiento preventivo programado por fecha o por kilometraje (HU9)."""

    id: int
    vehiculo_id: int
    tipo: str
    criterio: str
    fecha_programada: date | None = None
    kilometraje_objetivo: int | None = None
    cumplido: bool = False
    fecha_cumplimiento: date | None = None
    kilometraje_cumplimiento: int | None = None

    @property
    def es_por_fecha(self) -> bool:
        return self.criterio == CriterioMantenimiento.FECHA

    @property
    def es_por_kilometraje(self) -> bool:
        return self.criterio == CriterioMantenimiento.KILOMETRAJE

    @property
    def objetivo_texto(self) -> str:
        """Descripción legible del criterio, usada en plantillas y alertas."""
        if self.es_por_fecha and self.fecha_programada:
            return f"Por fecha — {self.fecha_programada:%d/%m/%Y}"
        if self.kilometraje_objetivo is not None:
            return f"Por kilometraje — {self.kilometraje_objetivo:,} km".replace(",", ".")
        return "—"


@dataclass(slots=True)
class Vehiculo:
    """Vehículo de la flota de un administrador (HU3)."""

    id: int
    usuario_id: int
    placa: str
    tipo: str
    marca: str
    modelo: str
    anio: int
    kilometraje_actual: int
    vencimiento_soat: date | None = None
    vencimiento_tecnomecanica: date | None = None
    fecha_ultima_lectura: date | None = None
    activo: bool = True

    @property
    def descripcion(self) -> str:
        """Etiqueta corta del vehículo: 'Chevrolet Spark 2019'."""
        return f"{self.marca} {self.modelo} {self.anio}"

    @property
    def es_motocicleta(self) -> bool:
        return self.tipo == TipoVehiculo.MOTOCICLETA

    def dar_de_baja(self) -> bool:
        """
        Desactivación lógica que conserva documentos e historial (HU6).

        Devuelve False si el vehículo ya estaba inactivo, para que la vista no
        confirme una baja que en realidad no ocurrió.
        """
        if not self.activo:
            return False
        self.activo = False
        return True