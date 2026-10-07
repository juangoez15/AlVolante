"""Formulario de configuración de alertas automáticas (HU11)."""

from __future__ import annotations

from django import forms

from flota.constants import UMBRALES_DIAS_DISPONIBLES, Mensajes
from flota.forms.base import CLASE_CHECK, FormularioBase, entrada, numero, validar_correo


class AlertasForm(FormularioBase):
    """Define cuándo y a quién se notifican los vencimientos próximos."""

    umbrales_dias = forms.MultipleChoiceField(
        label="Umbrales de alerta por fecha",
        choices=[(str(d), f"{d} días antes del vencimiento") for d in UMBRALES_DIAS_DISPONIBLES],
        widget=forms.CheckboxSelectMultiple(attrs={"class": CLASE_CHECK}),
        error_messages={"required": Mensajes.UMBRAL_REQUERIDO},
    )
    umbral_km = forms.IntegerField(
        label="Umbral de alerta por kilometraje (km de anticipación)",
        min_value=1,
        widget=numero("500"),
        error_messages={"invalid": "El umbral por kilometraje solo acepta valores numéricos"},
    )
    correo_notificaciones = forms.CharField(
        label="Correo para notificaciones",
        widget=entrada("administrador@empresa.com"),
        error_messages={"required": Mensajes.CORREO_INVALIDO},
    )

    def clean_umbrales_dias(self) -> list[int]:
        """Del más amplio al más cercano; el mayor define 'próximo a vencer'."""
        return sorted((int(v) for v in self.cleaned_data["umbrales_dias"]), reverse=True)

    def clean_correo_notificaciones(self) -> str:
        return validar_correo(self.cleaned_data["correo_notificaciones"])
