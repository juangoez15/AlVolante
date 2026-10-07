"""Casos de uso de autenticación y perfil (HU1, HU13)."""

from __future__ import annotations

from dataclasses import dataclass

from flota.domain.entities import Usuario
from flota.repositories import orm as memory  # O importa directamente orm
 # O si usas orm, asegúrate de importar el correcto


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
    usuario: Usuario, nombre: str, correo: str, password: str = "", avatar_file=None
) -> ResultadoPerfil:
    """
    Actualiza los datos del administrador y su avatar (HU13).

    Cambiar el correo o la contraseña invalida la sesión activa, porque son las
    credenciales con las que se inicia sesión.
    """
    requiere_reautenticacion = correo.lower() != usuario.correo.lower() or bool(password)

    usuario.nombre = nombre
    usuario.correo = correo
    if password:
        usuario.password = password

    # Llamamos al repositorio para actualizar los datos incluyendo el avatar
    # (Asegúrate de que 'memory.usuarios' u 'orm.usuarios' soporte el parámetro avatar_file)
    usuario_actualizado = memory.usuarios.actualizar(usuario, avatar_file=avatar_file)

    return ResultadoPerfil(usuario_actualizado or usuario, requiere_reautenticacion)
