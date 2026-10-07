"""
Constantes de dominio y mensajes de alVolante.

Centralizarlas evita literales repetidos en servicios, formularios y plantillas,
y garantiza que los textos coincidan con los criterios de aceptación.
"""

from __future__ import annotations

from enum import StrEnum


class TipoVehiculo(StrEnum):
    """Tipos admitidos al registrar un vehículo (HU3)."""

    AUTOMOVIL = "Automóvil"
    MOTOCICLETA = "Motocicleta"
    OTRO = "Otro"

    @classmethod
    def opciones(cls) -> list[tuple[str, str]]:
        return [(t.value, t.value) for t in cls]


class EstadoDocumento(StrEnum):
    """Estado de vigencia de SOAT y Tecnomecánica (HU8)."""

    VIGENTE = "Vigente"
    POR_VENCER = "Próximo a vencer"
    VENCIDO = "Vencido"
    SIN_REGISTRO = "Sin registro"


class EstadoMantenimiento(StrEnum):
    """Estado de un mantenimiento preventivo (HU9, HU10)."""

    PENDIENTE = "Pendiente"
    ATRASADO = "Atrasado"
    CUMPLIDO = "Cumplido"


class CriterioMantenimiento(StrEnum):
    """Criterio de programación; siempre uno solo, nunca ambos (HU9)."""

    FECHA = "fecha"
    KILOMETRAJE = "kilometraje"

    @classmethod
    def opciones(cls) -> list[tuple[str, str]]:
        return [(cls.FECHA.value, "Por fecha"), (cls.KILOMETRAJE.value, "Por kilometraje")]


#: Umbrales de anticipación seleccionables para las alertas por fecha (HU11).
UMBRALES_DIAS_DISPONIBLES: tuple[int, ...] = (30, 15, 5)

#: Valores por defecto de la configuración de alertas.
UMBRAL_DIAS_DEFECTO: int = 30
UMBRAL_KM_DEFECTO: int = 500

#: Cantidad de lecturas de kilometraje mostradas en el detalle (HU15).
LECTURAS_VISIBLES: int = 5


class Mensajes(StrEnum):
    """Textos de validación definidos en los criterios de aceptación."""

    CAMPOS_OBLIGATORIOS = "Debe completar los campos obligatorios"
    PLACA_DUPLICADA = "Ya existe un vehículo registrado con esta placa"
    CORREO_INVALIDO = "Verificar correo"
    CORREO_EN_USO = "Este correo ya está registrado"
    FECHA_INVALIDA = "Ingrese una fecha válida"
    CREDENCIALES_INVALIDAS = "El usuario o la contraseña son incorrectos"
    PASSWORD_CORTA = "La contraseña debe tener al menos 8 caracteres"
    SOLO_NUMEROS_ANIO = "El año solo acepta valores numéricos"
    SOLO_NUMEROS_KM = "El kilometraje solo acepta valores numéricos"
    FECHA_PASADA = "La fecha programada no puede ser anterior a la fecha actual"
    FECHA_FUTURA = "La fecha de lectura no puede ser posterior a la fecha actual"
    KM_MENOR = "El kilometraje no puede ser menor al último registrado"
    KM_OBJETIVO_INVALIDO = (
        "El kilometraje objetivo debe ser mayor al kilometraje actual del vehículo"
    )
    UMBRAL_REQUERIDO = "Debe seleccionar al menos un umbral de alerta"
    VEHICULO_INACTIVO = "Un vehículo dado de baja no admite modificaciones"
    MANTENIMIENTO_YA_CUMPLIDO = "Este mantenimiento ya fue marcado como cumplido"

    # Confirmaciones
    VEHICULO_CREADO = "Vehículo registrado exitosamente"
    VEHICULO_ACTUALIZADO = "Información actualizada exitosamente"
    DOCUMENTOS_ACTUALIZADOS = "Documentos actualizados exitosamente"
    MANTENIMIENTO_CREADO = "Mantenimiento registrado exitosamente"
    MANTENIMIENTO_CUMPLIDO = "Mantenimiento marcado como cumplido"
    KILOMETRAJE_REGISTRADO = "Kilometraje registrado exitosamente"
    CONFIGURACION_GUARDADA = "Configuración guardada exitosamente"
    PERFIL_ACTUALIZADO = "Perfil actualizado exitosamente"
