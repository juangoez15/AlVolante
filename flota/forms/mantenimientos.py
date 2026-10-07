"""Formulario de programación de mantenimiento preventivo (HU9)."""

from __future__ import annotations

from datetime import date

from django import forms

from flota.constants import CriterioMantenimiento, Mensajes
from flota.forms.base import CLASE_CHECK, FormularioBase, entrada, fecha, numero


class MantenimientoForm(FormularioBase):
    """
    Programa un mantenimiento por fecha o por kilometraje.

    El criterio es excluyente: se valida solo el campo correspondiente y el otro
    se descarta, de modo que nunca queden ambos objetivos guardados.
    """

    tipo = forms.CharField(label="Tipo de mantenimiento", widget=entrada("Cambio de aceite"))
    criterio = forms.ChoiceField(
        label="Criterio de programación",
        choices=CriterioMantenimiento.opciones(),
        initial=CriterioMantenimiento.FECHA,
        widget=forms.RadioSelect(attrs={"class": CLASE_CHECK}),
    )
    fecha_programada = forms.DateField(
        label="Fecha programada",
        required=False,
        widget=fecha(),
        error_messages={"invalid": Mensajes.FECHA_INVALIDA},
    )
    kilometraje_objetivo = forms.IntegerField(
        label="Kilometraje objetivo", required=False, min_value=0, widget=numero("50.000")
    )

    def __init__(self, *args, vehiculo=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.vehiculo = vehiculo

    def clean_tipo(self) -> str:
        return self.cleaned_data["tipo"].strip()

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("criterio") == CriterioMantenimiento.FECHA:
            self._validar_por_fecha(cleaned)
        else:
            self._validar_por_kilometraje(cleaned)
        return cleaned

    def _validar_por_fecha(self, cleaned: dict) -> None:
        cleaned["kilometraje_objetivo"] = None
        fecha_programada = cleaned.get("fecha_programada")

        if fecha_programada is None:
            self.add_error("fecha_programada", Mensajes.CAMPOS_OBLIGATORIOS)
        elif fecha_programada < date.today():
            self.add_error("fecha_programada", Mensajes.FECHA_PASADA)

    def _validar_por_kilometraje(self, cleaned: dict) -> None:
        cleaned["fecha_programada"] = None
        objetivo = cleaned.get("kilometraje_objetivo")

        if objetivo is None:
            self.add_error("kilometraje_objetivo", Mensajes.CAMPOS_OBLIGATORIOS)
        elif self.vehiculo and objetivo <= self.vehiculo.kilometraje_actual:
            self.add_error("kilometraje_objetivo", Mensajes.KM_OBJETIVO_INVALIDO)
