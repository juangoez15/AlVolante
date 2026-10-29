"""Casos de uso de autenticación y perfil (HU1, HU13)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import timedelta

from django.utils import timezone

from flota.domain.entities import Usuario
from flota.repositories import orm as memory


@dataclass(frozen=True, slots=True)
class ResultadoPerfil:
    """Informa si el cambio obliga a volver a autenticarse."""

    usuario: Usuario
    requiere_reautenticacion: bool


MAX_INTENTOS_FALLIDOS = 3
MINUTOS_BLOQUEO = 15


class CuentaBloqueada(Exception):
    """La cuenta superó los intentos fallidos y está bloqueada temporalmente."""

    def __init__(self, minutos: int):
        super().__init__(minutos)
        self.minutos = minutos


def autenticar(correo: str, password: str) -> Usuario | None:
    """Valida credenciales; al 3er intento fallido bloquea la cuenta 15 minutos (HU1)."""
    usuario = memory.usuarios.por_correo(correo)
    if usuario is None:
        return None

    ahora = timezone.now()
    if usuario.bloqueado_hasta and usuario.bloqueado_hasta > ahora:
        restante = usuario.bloqueado_hasta - ahora
        raise CuentaBloqueada(max(1, math.ceil(restante.total_seconds() / 60)))

    # El bloqueo ya venció: se parte de cero.
    intentos = 0 if usuario.bloqueado_hasta else usuario.intentos_fallidos

    if usuario.password != password:
        intentos += 1
        if intentos >= MAX_INTENTOS_FALLIDOS:
            memory.usuarios.actualizar_bloqueo(
                usuario.id, 0, ahora + timedelta(minutes=MINUTOS_BLOQUEO)
            )
            raise CuentaBloqueada(MINUTOS_BLOQUEO)
        memory.usuarios.actualizar_bloqueo(usuario.id, intentos, None)
        return None

    if intentos or usuario.bloqueado_hasta:
        memory.usuarios.actualizar_bloqueo(usuario.id, 0, None)
    return usuario


def actualizar_perfil(
    usuario: Usuario, nombre: str, correo: str, password: str = ""
) -> ResultadoPerfil:
    """Actualiza los datos del administrador (HU13)."""
    requiere_reautenticacion = correo.lower() != usuario.correo.lower() or bool(password)

    usuario.nombre = nombre
    usuario.correo = correo
    if password:
        usuario.password = password

    usuario_actualizado = memory.usuarios.guardar(usuario)

    return ResultadoPerfil(usuario_actualizado or usuario, requiere_reautenticacion)


def actualizar_avatar(usuario: Usuario, avatar_file) -> Usuario:
    """Actualiza exclusivamente el avatar del usuario por separado."""
    if avatar_file:
        usuario_actualizado = memory.usuarios.actualizar(usuario, avatar_file=avatar_file)
        return usuario_actualizado
    return usuario