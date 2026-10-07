"""
Envío diario de alertas de vencimiento (HU11).

    python manage.py enviar_alertas --dry-run   # solo muestra en consola
    python manage.py enviar_alertas             # envía el correo

Programación sugerida:

    0 7 * * * cd /ruta/alvolante && python manage.py enviar_alertas

Las alertas se emiten mientras el vencimiento esté dentro de la ventana
configurada, no únicamente el día exacto del umbral: si el cron no corre un
día, la notificación no se pierde. Ante un fallo de envío se registra el error
y se reintenta al día siguiente; el panel (HU12) sigue siendo la fuente de
verdad.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date

from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandParser

from flota.constants import EstadoMantenimiento
from flota.domain import rules
from flota.domain.entities import Configuracion, Vehiculo
from flota.repositories import memory

logger = logging.getLogger(__name__)

ASUNTO = "alVolante — Vencimientos próximos de su flota"
ENCABEZADO = "alVolante — Alertas de vencimiento"


@dataclass(frozen=True, slots=True)
class Alerta:
    """Línea de notificación ya formateada."""

    etiqueta: str
    detalle: str

    def __str__(self) -> str:
        return f"[{self.etiqueta}] {self.detalle}"


class Command(BaseCommand):
    help = "Revisa vencimientos de documentos y mantenimientos, y envía las alertas."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Muestra las alertas en consola sin enviar el correo.",
        )

    def handle(self, *args, **opciones) -> None:
        hoy = date.today()
        config = memory.configuracion.obtener()
        alertas = self._recolectar(config, hoy)

        if not alertas:
            self.stdout.write(self.style.SUCCESS("Sin vencimientos próximos para notificar."))
            return

        cuerpo = f"{ENCABEZADO}\n\n" + "\n".join(str(a) for a in alertas)

        if opciones["dry_run"]:
            self.stdout.write(cuerpo)
            return

        self._enviar(cuerpo, config, total=len(alertas))

    # -- Recolección --------------------------------------------------------

    def _recolectar(self, config: Configuracion, hoy: date) -> list[Alerta]:
        """Recorre la flota activa de cada administrador."""
        alertas: list[Alerta] = []
        for usuario in memory.usuarios.listar():
            for vehiculo in memory.vehiculos.listar(usuario.id):
                alertas += self._alertas_documentos(vehiculo, config, hoy)
                alertas += self._alertas_mantenimientos(vehiculo, config, hoy)
        return alertas

    def _alertas_documentos(
        self, vehiculo: Vehiculo, config: Configuracion, hoy: date
    ) -> list[Alerta]:
        """Vencimientos de SOAT y Tecnomecánica dentro de la ventana (HU7)."""
        alertas: list[Alerta] = []
        documentos = (
            ("SOAT", vehiculo.vencimiento_soat),
            ("Revisión Tecnomecánica", vehiculo.vencimiento_tecnomecanica),
        )

        for nombre, vencimiento in documentos:
            if vencimiento is None:
                continue
            dias = (vencimiento - hoy).days
            if dias < 0:
                alertas.append(
                    Alerta(
                        "VENCIDO",
                        f"{vehiculo.placa} — {nombre} venció el {vencimiento:%d/%m/%Y}",
                    )
                )
            elif dias <= config.umbral_mayor:
                alertas.append(
                    Alerta(
                        f"{dias} días",
                        f"{vehiculo.placa} — {nombre} vence el {vencimiento:%d/%m/%Y}",
                    )
                )
        return alertas

    def _alertas_mantenimientos(
        self, vehiculo: Vehiculo, config: Configuracion, hoy: date
    ) -> list[Alerta]:
        """Mantenimientos atrasados o próximos por fecha o kilometraje (HU9)."""
        alertas: list[Alerta] = []

        for mantenimiento in memory.mantenimientos.listar(vehiculo.id, cumplidos=False):
            estado = rules.estado_mantenimiento(mantenimiento, vehiculo.kilometraje_actual, hoy)

            if estado is EstadoMantenimiento.ATRASADO:
                alertas.append(
                    Alerta(
                        "ATRASADO",
                        f"{vehiculo.placa} — {mantenimiento.tipo} "
                        f"({mantenimiento.objetivo_texto})",
                    )
                )
                continue

            if mantenimiento.es_por_fecha and mantenimiento.fecha_programada:
                dias = (mantenimiento.fecha_programada - hoy).days
                if dias <= config.umbral_mayor:
                    alertas.append(
                        Alerta(
                            f"{dias} días",
                            f"{vehiculo.placa} — {mantenimiento.tipo} programado para "
                            f"{mantenimiento.fecha_programada:%d/%m/%Y}",
                        )
                    )
            elif mantenimiento.kilometraje_objetivo is not None:
                restantes = mantenimiento.kilometraje_objetivo - vehiculo.kilometraje_actual
                if 0 <= restantes <= config.umbral_km:
                    alertas.append(
                        Alerta(
                            f"{restantes} km",
                            f"{vehiculo.placa} — {mantenimiento.tipo} a los "
                            f"{mantenimiento.kilometraje_objetivo} km",
                        )
                    )
        return alertas

    # -- Envío --------------------------------------------------------------

    def _enviar(self, cuerpo: str, config: Configuracion, total: int) -> None:
        destinatario = config.correo_notificaciones
        try:
            send_mail(
                subject=ASUNTO,
                message=cuerpo,
                from_email=None,
                recipient_list=[destinatario],
                fail_silently=False,
            )
        except Exception as error:  # noqa: BLE001 — se reintenta al día siguiente
            logger.exception("Falló el envío de alertas de alVolante")
            self.stderr.write(f"Falló el envío de alertas: {error}")
            return

        self.stdout.write(self.style.SUCCESS(f"{total} alertas enviadas a {destinatario}"))
