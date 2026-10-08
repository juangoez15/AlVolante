"""Vistas de alVolante, agrupadas por historia de usuario."""

from flota.views.configuracion import alertas
from flota.views.cuentas import login, logout, perfil
from flota.views.kilometraje import registrar as registrar_kilometraje
from flota.views.mantenimientos import marcar_cumplido, programar
from flota.views.panel import panel
from flota.views.vehiculos import crear, dar_de_baja, detalle, documentos, editar, listar, reactivar

__all__ = [
    "alertas",
    "crear",
    "dar_de_baja",
    "detalle",
    "documentos",
    "editar",
    "listar",
    "login",
    "logout",
    "marcar_cumplido",
    "panel",
    "perfil",
    "programar",
    "reactivar",
    "registrar_kilometraje",
]