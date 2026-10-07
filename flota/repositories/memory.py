"""
Repositorios en memoria.

Única capa con conocimiento de cómo se almacenan los datos. Los servicios
dependen de estas interfaces, nunca de las estructuras internas, de modo que
migrar a PostgreSQL consiste en reimplementar estas clases sobre el ORM sin
tocar dominio, servicios, vistas ni plantillas.

Advertencia: los datos viven en variables de proceso y se reinician con el
servidor. El `Lock` protege los contadores de id frente al servidor multihilo
de desarrollo.
"""

from __future__ import annotations

import threading
from datetime import date
from itertools import count

from flota.domain.entities import (
    Configuracion,
    LecturaKilometraje,
    Mantenimiento,
    Usuario,
    Vehiculo,
)


class _SecuenciaId:
    """Generador de identificadores incrementales seguro entre hilos."""

    def __init__(self) -> None:
        self._contador = count(1)
        self._lock = threading.Lock()

    def siguiente(self) -> int:
        with self._lock:
            return next(self._contador)


class UsuarioRepository:
    """Cuentas de administrador de flota (HU1, HU13)."""

    def __init__(self) -> None:
        self._usuarios: list[Usuario] = []
        self._ids = _SecuenciaId()

    def listar(self) -> list[Usuario]:
        return list(self._usuarios)

    def obtener(self, usuario_id: int) -> Usuario | None:
        return next((u for u in self._usuarios if u.id == usuario_id), None)

    def por_correo(self, correo: str) -> Usuario | None:
        correo = correo.strip().lower()
        return next((u for u in self._usuarios if u.correo.lower() == correo), None)

    def correo_en_uso(self, correo: str, excluir_id: int | None = None) -> bool:
        usuario = self.por_correo(correo)
        return usuario is not None and usuario.id != excluir_id

    def crear(self, nombre: str, correo: str, password: str) -> Usuario:
        usuario = Usuario(
            id=self._ids.siguiente(),
            nombre=nombre,
            correo=correo,
            password=password,
        )
        self._usuarios.append(usuario)
        return usuario


class VehiculoRepository:
    """Vehículos, siempre consultados dentro de la flota de un usuario."""

    def __init__(self) -> None:
        self._vehiculos: list[Vehiculo] = []
        self._ids = _SecuenciaId()

    def listar(
        self,
        usuario_id: int,
        *,
        solo_activos: bool = True,
        placa_contiene: str = "",
    ) -> list[Vehiculo]:
        resultado = (v for v in self._vehiculos if v.usuario_id == usuario_id)
        if solo_activos:
            resultado = (v for v in resultado if v.activo)
        if placa_contiene:
            termino = placa_contiene.strip().upper()
            resultado = (v for v in resultado if termino in v.placa)
        return sorted(resultado, key=lambda v: v.placa)

    def obtener(self, vehiculo_id: int, usuario_id: int) -> Vehiculo | None:
        """Filtra por usuario para aislar flotas incluso al entrar por URL."""
        return next(
            (v for v in self._vehiculos if v.id == vehiculo_id and v.usuario_id == usuario_id),
            None,
        )

    def placa_en_uso(self, placa: str, usuario_id: int, excluir_id: int | None = None) -> bool:
        placa = placa.strip().upper()
        return any(
            v.placa == placa and v.usuario_id == usuario_id and v.id != excluir_id
            for v in self._vehiculos
        )

    def agregar(self, vehiculo: Vehiculo) -> Vehiculo:
        vehiculo.id = self._ids.siguiente()
        self._vehiculos.append(vehiculo)
        return vehiculo


class MantenimientoRepository:
    """Mantenimientos preventivos de cada vehículo (HU9, HU10)."""

    def __init__(self) -> None:
        self._mantenimientos: list[Mantenimiento] = []
        self._ids = _SecuenciaId()

    def listar(self, vehiculo_id: int, *, cumplidos: bool | None = None):
        items = [m for m in self._mantenimientos if m.vehiculo_id == vehiculo_id]
        if cumplidos is not None:
            items = [m for m in items if m.cumplido is cumplidos]
        return sorted(items, key=lambda m: m.id)

    def obtener(self, mantenimiento_id: int, vehiculo_id: int) -> Mantenimiento | None:
        return next(
            (
                m
                for m in self._mantenimientos
                if m.id == mantenimiento_id and m.vehiculo_id == vehiculo_id
            ),
            None,
        )

    def agregar(self, mantenimiento: Mantenimiento) -> Mantenimiento:
        mantenimiento.id = self._ids.siguiente()
        self._mantenimientos.append(mantenimiento)
        return mantenimiento


class LecturaRepository:
    """Histórico de lecturas del odómetro (HU14)."""

    def __init__(self) -> None:
        self._lecturas: list[LecturaKilometraje] = []
        self._ids = _SecuenciaId()

    def historico(self, vehiculo_id: int) -> list[LecturaKilometraje]:
        """Lecturas de la más reciente a la más antigua."""
        lecturas = [l for l in self._lecturas if l.vehiculo_id == vehiculo_id]
        return sorted(lecturas, key=lambda l: (l.fecha_lectura, l.id), reverse=True)

    def ultima(self, vehiculo_id: int) -> LecturaKilometraje | None:
        historico = self.historico(vehiculo_id)
        return historico[0] if historico else None

    def agregar(self, vehiculo_id: int, kilometraje: int, fecha_lectura: date):
        lectura = LecturaKilometraje(
            id=self._ids.siguiente(),
            vehiculo_id=vehiculo_id,
            kilometraje=kilometraje,
            fecha_lectura=fecha_lectura,
        )
        self._lecturas.append(lectura)
        return lectura


class ConfiguracionRepository:
    """Configuración única de alertas del sistema (HU11)."""

    def __init__(self) -> None:
        self._configuracion = Configuracion()

    def obtener(self) -> Configuracion:
        return self._configuracion

    def guardar(
        self, *, umbrales_dias: list[int], umbral_km: int, correo_notificaciones: str
    ) -> Configuracion:
        config = self._configuracion
        config.umbrales_dias = sorted(umbrales_dias, reverse=True)
        config.umbral_km = umbral_km
        config.correo_notificaciones = correo_notificaciones
        return config


# Instancias compartidas por toda la aplicación.
usuarios = UsuarioRepository()
vehiculos = VehiculoRepository()
mantenimientos = MantenimientoRepository()
lecturas = LecturaRepository()
configuracion = ConfiguracionRepository()
