"""Formularios de autenticación y perfil (HU1, HU13)."""

from __future__ import annotations

from django import forms

from flota.constants import Mensajes
from flota.forms.base import CLASE_INPUT, FormularioBase, entrada, validar_correo
from flota.repositories import memory

LONGITUD_MINIMA_PASSWORD = 8


def _password(placeholder: str = "••••••••") -> forms.PasswordInput:
    return forms.PasswordInput(attrs={"class": CLASE_INPUT, "placeholder": placeholder})


class LoginForm(forms.Form):
    """Credenciales de acceso. No hay registro público ni recuperación (HU1)."""

    correo = forms.CharField(
        label="Correo electrónico",
        widget=entrada("administrador@empresa.com", autofocus=True),
        error_messages={"required": Mensajes.CORREO_INVALIDO},
    )
    password = forms.CharField(
        label="Contraseña",
        widget=_password(),
        error_messages={"required": "Debe ingresar su contraseña"},
    )

    def clean_correo(self) -> str:
        return validar_correo(self.cleaned_data["correo"])


class PerfilForm(FormularioBase):
    """Datos del administrador. La contraseña solo cambia si se diligencia."""

    nombre = forms.CharField(label="Nombre completo", widget=entrada("Administrador de flota"))
    correo = forms.CharField(
        label="Correo electrónico",
        widget=entrada("administrador@empresa.com"),
        error_messages={"required": Mensajes.CORREO_INVALIDO},
    )
    password = forms.CharField(
        label="Nueva contraseña", required=False, widget=_password()
    )
    avatar = forms.ImageField(required=False)

    def __init__(self, *args, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.usuario = usuario

    def clean_correo(self) -> str:
        correo = validar_correo(self.cleaned_data["correo"])
        excluir = self.usuario.id if self.usuario else None
        if memory.usuarios.correo_en_uso(correo, excluir_id=excluir):
            raise forms.ValidationError(Mensajes.CORREO_EN_USO)
        return correo

    def clean_password(self) -> str:
        password = self.cleaned_data.get("password", "")
        if password and len(password) < LONGITUD_MINIMA_PASSWORD:
            raise forms.ValidationError(Mensajes.PASSWORD_CORTA)
        return password