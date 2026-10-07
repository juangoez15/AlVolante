"""
Autenticación propia, sin base de datos (HU1, HU2).

`django.contrib.auth` exige tablas, por lo que en esta etapa la sesión se
reduce al id del administrador guardado en una cookie firmada. Al migrar a
PostgreSQL, este módulo se sustituye por `django.contrib.auth` y los
decoradores de `flota.decorators` pasan a envolver `login_required`.
"""

from __future__ import annotations

from django.http import HttpRequest

from flota.domain.entities import Usuario
from flota.repositories import memory

CLAVE_SESION = "alvolante_usuario_id"


def iniciar_sesion(request: HttpRequest, usuario: Usuario) -> None:
    """Abre sesión rotando la clave para evitar fijación de sesión."""
    request.session.cycle_key()
    request.session[CLAVE_SESION] = usuario.id


def cerrar_sesion(request: HttpRequest) -> None:
    """Descarta la sesión completa (HU2)."""
    request.session.flush()


def usuario_autenticado(request: HttpRequest) -> Usuario | None:
    """Administrador de la sesión actual, o None si no hay sesión válida."""
    usuario_id = request.session.get(CLAVE_SESION)
    return memory.usuarios.obtener(usuario_id) if usuario_id else None
