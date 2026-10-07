"""Utilidades compartidas por los formularios de alVolante."""

from __future__ import annotations

import re

from django import forms

from flota.constants import Mensajes

#: Validación pragmática de correo: algo@algo.tld, sin espacios.
PATRON_CORREO = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

CLASE_INPUT = "form-control"
CLASE_SELECT = "form-select"
CLASE_CHECK = "form-check-input"


def entrada(placeholder: str = "", **attrs) -> forms.TextInput:
    return forms.TextInput(attrs={"class": CLASE_INPUT, "placeholder": placeholder, **attrs})


def numero(placeholder: str = "", **attrs) -> forms.NumberInput:
    return forms.NumberInput(attrs={"class": CLASE_INPUT, "placeholder": placeholder, **attrs})


def fecha(**attrs) -> forms.DateInput:
    return forms.DateInput(attrs={"class": CLASE_INPUT, "type": "date", **attrs}, format="%Y-%m-%d")


def seleccion(**attrs) -> forms.Select:
    return forms.Select(attrs={"class": CLASE_SELECT, **attrs})


def validar_correo(valor: str) -> str:
    """Normaliza y valida un correo, con el mensaje de los criterios."""
    correo = valor.strip()
    if not PATRON_CORREO.match(correo):
        raise forms.ValidationError(Mensajes.CORREO_INVALIDO)
    return correo


#: Texto que Django asigna por defecto a los campos obligatorios.
_REQUERIDO_POR_DEFECTO = forms.Field().error_messages["required"]


class FormularioBase(forms.Form):
    """
    Formulario con el mensaje unificado de campos obligatorios (HU3, HU5).

    El mensaje se fija en `error_messages['required']` durante la construcción.
    Reescribir `self.errors` en `clean()` sería frágil, porque obligaría a
    detectar el texto por defecto de Django y dejaría de funcionar al cambiar
    el idioma del proyecto.

    Solo se reemplaza el mensaje genérico: los campos que declaran uno propio
    (por ejemplo el umbral de alertas en HU11) conservan su texto específico.
    """

    mensaje_requerido: str = Mensajes.CAMPOS_OBLIGATORIOS

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            if not campo.required:
                continue
            if campo.error_messages.get("required") == _REQUERIDO_POR_DEFECTO:
                campo.error_messages["required"] = self.mensaje_requerido
