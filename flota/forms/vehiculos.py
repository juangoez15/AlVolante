"""Formularios de vehículos, documentos y kilometraje (HU3, HU5, HU7, HU14)."""

from __future__ import annotations

from datetime import date

from django import forms

from flota.constants import Mensajes, TipoVehiculo
from flota.forms.base import FormularioBase, entrada, fecha, numero, seleccion
from flota.repositories import memory
from flota.services import kilometraje as servicio_kilometraje

ANIO_MINIMO = 1900


class VehiculoForm(FormularioBase):
    """Alta y edición de vehículo; comparte campos y validaciones (HU3, HU5)."""

    placa = forms.CharField(label="Placa", widget=entrada("ABC123"))
    tipo = forms.ChoiceField(
        label="Tipo de vehículo",
        choices=[("", "Seleccione...")] + TipoVehiculo.opciones(),
        widget=seleccion(),
    )
    marca = forms.CharField(label="Marca", widget=entrada("Chevrolet"))
    modelo = forms.CharField(label="Modelo", widget=entrada("Spark"))
    anio = forms.IntegerField(
        label="Año",
        min_value=ANIO_MINIMO,
        max_value=date.today().year + 1,
        widget=numero("2020"),
        error_messages={"invalid": Mensajes.SOLO_NUMEROS_ANIO},
    )
    kilometraje_actual = forms.IntegerField(
        label="Kilometraje actual",
        min_value=0,
        widget=numero("45.000 km"),
        error_messages={"invalid": Mensajes.SOLO_NUMEROS_KM},
    )

    def __init__(self, *args, usuario_id: int, vehiculo_id: int | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.usuario_id = usuario_id
        self.vehiculo_id = vehiculo_id

    def clean_placa(self) -> str:
        """La placa es única dentro de la flota del administrador."""
        placa = self.cleaned_data["placa"].strip().upper()
        if memory.vehiculos.placa_en_uso(placa, self.usuario_id, excluir_id=self.vehiculo_id):
            raise forms.ValidationError(Mensajes.PLACA_DUPLICADA)
        return placa

    def clean_marca(self) -> str:
        return self.cleaned_data["marca"].strip()

    def clean_modelo(self) -> str:
        return self.cleaned_data["modelo"].strip()


class DocumentosForm(forms.Form):
    """Fechas de vencimiento, registradas manualmente sin validar contra el RUNT (HU7)."""

    vencimiento_soat = forms.DateField(
        label="Fecha de vencimiento del SOAT",
        widget=fecha(),
        error_messages={"required": Mensajes.FECHA_INVALIDA, "invalid": Mensajes.FECHA_INVALIDA},
    )
    vencimiento_tecnomecanica = forms.DateField(
        label="Fecha de vencimiento de la Revisión Tecnomecánica",
        widget=fecha(),
        error_messages={"required": Mensajes.FECHA_INVALIDA, "invalid": Mensajes.FECHA_INVALIDA},
    )


class KilometrajeForm(FormularioBase):
    """Lectura manual del odómetro; nunca decrece ni se registra a futuro (HU14)."""

    vehiculo_id = forms.ChoiceField(label="Vehículo", choices=(), widget=seleccion())
    kilometraje = forms.IntegerField(
        label="Kilometraje actual (km)",
        min_value=0,
        widget=numero("46.253"),
        error_messages={"invalid": "El kilometraje solo acepta valores numéricos enteros"},
    )
    fecha_lectura = forms.DateField(
        label="Fecha de lectura",
        widget=fecha(),
        error_messages={"required": Mensajes.FECHA_INVALIDA, "invalid": Mensajes.FECHA_INVALIDA},
    )

    def __init__(self, *args, vehiculos=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._vehiculos = {str(v.id): v for v in (vehiculos or [])}
        self.fields["vehiculo_id"].choices = [
            (str(v.id), f"{v.placa} — {v.descripcion}") for v in self._vehiculos.values()
        ]

    @property
    def vehiculo(self):
        """Vehículo seleccionado, disponible tras validar."""
        return self._vehiculos.get(self.cleaned_data.get("vehiculo_id", ""))

    def clean_fecha_lectura(self) -> date:
        fecha_lectura = self.cleaned_data["fecha_lectura"]
        if fecha_lectura > date.today():
            raise forms.ValidationError(Mensajes.FECHA_FUTURA)
        return fecha_lectura

    def clean(self):
        cleaned = super().clean()
        vehiculo = self._vehiculos.get(cleaned.get("vehiculo_id", ""))
        kilometraje = cleaned.get("kilometraje")

        if vehiculo is not None and kilometraje is not None:
            if kilometraje < servicio_kilometraje.kilometraje_de_referencia(vehiculo):
                self.add_error("kilometraje", Mensajes.KM_MENOR)
        return cleaned
