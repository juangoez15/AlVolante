"""Casos de uso de autenticación y perfil (HU1, HU13)."""

from __future__ import annotations

from dataclasses import dataclass

from flota.domain.entities import Usuario
from flota.repositories import orm as memory


@dataclass(frozen=True, slots=True)
class ResultadoPerfil:
    """Informa si el cambio obliga a volver a autenticarse."""

    usuario: Usuario
    requiere_reautenticacion: bool


def autenticar(correo: str, password: str) -> Usuario | None:
    """Valida credenciales contra las cuentas registradas (HU1)."""
    usuario = memory.usuarios.por_correo(correo)
    if usuario is None or usuario.password != password:
        return None
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