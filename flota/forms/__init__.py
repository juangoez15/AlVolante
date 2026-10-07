"""Formularios de alVolante, agrupados por área funcional."""

from flota.forms.configuracion import AlertasForm
from flota.forms.cuentas import LoginForm, PerfilForm
from flota.forms.mantenimientos import MantenimientoForm
from flota.forms.vehiculos import DocumentosForm, KilometrajeForm, VehiculoForm

__all__ = [
    "AlertasForm",
    "DocumentosForm",
    "KilometrajeForm",
    "LoginForm",
    "MantenimientoForm",
    "PerfilForm",
    "VehiculoForm",
]
