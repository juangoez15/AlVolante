"""
Datos iniciales de demostración.

Reproducen los vehículos de los prototipos para que la aplicación sea navegable
al arrancar. Se cargan una sola vez desde `FlotaConfig.ready()`; al desaparecer
el almacenamiento en memoria con PostgreSQL, este módulo se reemplaza por una
migración de datos o un fixture.
"""

from __future__ import annotations

from datetime import date, timedelta

from flota.constants import CriterioMantenimiento, TipoVehiculo
from flota.domain.entities import Mantenimiento, Vehiculo
from flota.repositories import memory

CORREO_DEMO = "administrador@empresa.com"
PASSWORD_DEMO = "alvolante2026"

# placa, tipo, marca, modelo, año, km, días para vencer SOAT, días para Tecnomecánica
_VEHICULOS_DEMO = (
    ("ABC123", TipoVehiculo.AUTOMOVIL, "Chevrolet", "Spark", 2019, 46_250, 22, 400),
    ("XYZ987", TipoVehiculo.MOTOCICLETA, "Yamaha", "FZ", 2021, 18_400, -12, 260),
    ("QWE456", TipoVehiculo.AUTOMOVIL, "Renault", "Duster", 2020, 87_300, 180, 25),
    ("RTY321", TipoVehiculo.AUTOMOVIL, "Mazda", "2", 2022, 31_200, 300, 210),
)


def cargar_datos_demo() -> None:
    """Siembra la cuenta y la flota de ejemplo si el repositorio está vacío."""
    if memory.usuarios.listar():
        return

    hoy = date.today()
    admin = memory.usuarios.crear("Henry Gil Agudelo", CORREO_DEMO, PASSWORD_DEMO)

    for placa, tipo, marca, modelo, anio, km, dias_soat, dias_tecno in _VEHICULOS_DEMO:
        vehiculo = memory.vehiculos.agregar(
            Vehiculo(
                id=0,  # lo asigna el repositorio
                usuario_id=admin.id,
                placa=placa,
                tipo=tipo,
                marca=marca,
                modelo=modelo,
                anio=anio,
                kilometraje_actual=km,
                vencimiento_soat=hoy + timedelta(days=dias_soat),
                vencimiento_tecnomecanica=hoy + timedelta(days=dias_tecno),
                fecha_ultima_lectura=hoy - timedelta(days=6),
            )
        )
        memory.lecturas.agregar(vehiculo.id, km, hoy - timedelta(days=6))

    _cargar_mantenimientos_demo(hoy)


def _cargar_mantenimientos_demo(hoy: date) -> None:
    """Cubre los tres estados: pendiente, atrasado y cumplido."""
    memory.mantenimientos.agregar(
        Mantenimiento(
            id=0,
            vehiculo_id=1,
            tipo="Cambio de aceite",
            criterio=CriterioMantenimiento.FECHA,
            fecha_programada=hoy + timedelta(days=17),
        )
    )
    memory.mantenimientos.agregar(
        Mantenimiento(
            id=0,
            vehiculo_id=1,
            tipo="Revisión de frenos",
            criterio=CriterioMantenimiento.KILOMETRAJE,
            kilometraje_objetivo=46_000,  # ya superado: queda atrasado
        )
    )
    memory.mantenimientos.agregar(
        Mantenimiento(
            id=0,
            vehiculo_id=1,
            tipo="Alineación y balanceo",
            criterio=CriterioMantenimiento.KILOMETRAJE,
            kilometraje_objetivo=50_000,
        )
    )
    memory.mantenimientos.agregar(
        Mantenimiento(
            id=0,
            vehiculo_id=1,
            tipo="Cambio de llantas",
            criterio=CriterioMantenimiento.FECHA,
            fecha_programada=hoy - timedelta(days=60),
            cumplido=True,
            fecha_cumplimiento=hoy - timedelta(days=58),
            kilometraje_cumplimiento=41_040,
        )
    )
    memory.mantenimientos.agregar(
        Mantenimiento(
            id=0,
            vehiculo_id=3,
            tipo="Cambio de aceite",
            criterio=CriterioMantenimiento.FECHA,
            fecha_programada=hoy + timedelta(days=20),
        )
    )
