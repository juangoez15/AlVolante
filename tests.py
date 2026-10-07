"""
Pruebas de alVolante.

    python tests.py

Se ejecutan con el cliente de pruebas de Django sobre el repositorio en
memoria, sin necesidad de base de datos. Cubren las 15 historias de usuario,
los mensajes exactos de los criterios de aceptación y las regresiones
detectadas en la revisión de código.
"""

from __future__ import annotations

import os
import sys
from datetime import date, timedelta

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.test import Client  # noqa: E402

from flota.constants import EstadoDocumento, EstadoMantenimiento, Mensajes  # noqa: E402
from flota.domain import rules  # noqa: E402
from flota.repositories import memory  # noqa: E402
from flota.repositories.seed import CORREO_DEMO, PASSWORD_DEMO  # noqa: E402
from flota.services import mantenimientos as servicio_mantenimientos  # noqa: E402
from flota.services import panel as servicio_panel  # noqa: E402
from flota.services import vehiculos as servicio_vehiculos  # noqa: E402
from flota.templatetags.flota_extras import km as filtro_km  # noqa: E402

HOY = date.today()
MANANA = HOY + timedelta(days=1)
AYER = HOY - timedelta(days=1)

_fallos: list[str] = []


# ---------------------------------------------------------------------------
# Utilidades de aserción
# ---------------------------------------------------------------------------


def verificar(condicion: bool, descripcion: str) -> None:
    """Registra el resultado sin abortar la ejecución de las demás pruebas."""
    if condicion:
        print(f"  ✓ {descripcion}")
    else:
        print(f"  ✗ {descripcion}")
        _fallos.append(descripcion)


def contiene(respuesta, texto: str) -> bool:
    return texto.encode() in respuesta.content


def sesion_iniciada(correo: str = CORREO_DEMO, password: str = PASSWORD_DEMO) -> Client:
    cliente = Client()
    cliente.post("/", {"correo": correo, "password": password})
    return cliente


def datos_vehiculo(**sobrescribir) -> dict:
    base = {
        "placa": "TST001",
        "tipo": "Otro",
        "marca": "Kia",
        "modelo": "Rio",
        "anio": 2023,
        "kilometraje_actual": 1000,
    }
    return base | sobrescribir


# ---------------------------------------------------------------------------
# HU1, HU2, HU13 — Cuentas
# ---------------------------------------------------------------------------


def probar_autenticacion() -> None:
    print("\nHU1, HU2 — Autenticación")
    cliente = Client()

    verificar(cliente.get("/").status_code == 200, "El formulario de acceso responde")
    verificar(
        contiene(cliente.post("/", {"correo": "malo", "password": "x"}), Mensajes.CORREO_INVALIDO),
        "Rechaza un correo con formato inválido",
    )
    verificar(
        contiene(
            cliente.post("/", {"correo": "otro@empresa.com", "password": "x"}),
            Mensajes.CREDENCIALES_INVALIDAS,
        ),
        "Rechaza credenciales incorrectas",
    )
    verificar(
        cliente.post("/", {"correo": CORREO_DEMO, "password": PASSWORD_DEMO}).status_code == 302,
        "Inicia sesión con credenciales válidas",
    )
    verificar(cliente.get("/panel/").status_code == 200, "Accede al panel autenticado")
    cliente.get("/salir/")
    verificar(
        cliente.get("/panel/").status_code == 302, "Bloquea el panel tras cerrar sesión"
    )


def probar_perfil() -> None:
    print("\nHU13 — Perfil")
    cliente = sesion_iniciada()

    verificar(cliente.get("/perfil/").status_code == 200, "Muestra los datos del administrador")
    verificar(
        contiene(
            cliente.post("/perfil/", {"nombre": "Henry", "correo": "n@e.com", "password": "123"}),
            Mensajes.PASSWORD_CORTA,
        ),
        "Exige una contraseña de longitud mínima",
    )

    respuesta = cliente.post(
        "/perfil/", {"nombre": "Henry Gil", "correo": CORREO_DEMO, "password": ""}
    )
    verificar(respuesta.status_code == 302, "Guarda el perfil sin cambiar credenciales")
    verificar(
        cliente.get("/panel/").status_code == 200, "Conserva la sesión si no cambian credenciales"
    )

    cliente.post("/perfil/", {"nombre": "Henry Gil", "correo": CORREO_DEMO, "password": "clave12345"})
    verificar(
        cliente.get("/panel/").status_code == 302, "Cierra la sesión al cambiar la contraseña"
    )
    # Restablece la credencial para no afectar pruebas posteriores.
    memory.usuarios.por_correo(CORREO_DEMO).password = PASSWORD_DEMO


# ---------------------------------------------------------------------------
# HU3 a HU6 — Vehículos
# ---------------------------------------------------------------------------


def probar_vehiculos() -> None:
    print("\nHU3 a HU6 — Vehículos")
    cliente = sesion_iniciada()

    verificar(cliente.get("/vehiculos/").status_code == 200, "Lista la flota activa")
    verificar(cliente.get("/vehiculos/?q=ABC").status_code == 200, "Filtra por placa")

    vacio = cliente.post("/vehiculos/nuevo/", datos_vehiculo(placa="", tipo="", marca="", modelo="", anio="", kilometraje_actual=""))
    verificar(
        vacio.content.count(Mensajes.CAMPOS_OBLIGATORIOS.encode()) >= 6,
        "Marca todos los campos obligatorios vacíos",
    )
    verificar(
        contiene(cliente.post("/vehiculos/nuevo/", datos_vehiculo(placa="ABC123")), Mensajes.PLACA_DUPLICADA),
        "Impide placas duplicadas en la misma flota",
    )
    verificar(
        cliente.post("/vehiculos/nuevo/", datos_vehiculo()).status_code == 302,
        "Registra un vehículo válido",
    )

    vehiculo = memory.vehiculos.listar(1, placa_contiene="TST001")[0]
    verificar(cliente.get(f"/vehiculos/{vehiculo.id}/").status_code == 200, "Abre el detalle")
    verificar(
        cliente.post(
            f"/vehiculos/{vehiculo.id}/editar/", datos_vehiculo(marca="Hyundai")
        ).status_code == 302,
        "Actualiza los datos del vehículo",
    )
    verificar(cliente.get("/vehiculos/9999/").status_code == 404, "Devuelve 404 para otra flota")


def probar_baja() -> None:
    print("\nHU6 — Baja lógica")
    cliente = sesion_iniciada()
    vehiculo = memory.vehiculos.listar(1, placa_contiene="RTY321")[0]

    verificar(cliente.get(f"/vehiculos/{vehiculo.id}/baja/").status_code == 200, "Pide confirmación")
    verificar(cliente.post(f"/vehiculos/{vehiculo.id}/baja/").status_code == 302, "Da de baja")
    verificar(not vehiculo.activo, "El vehículo queda inactivo")
    verificar(
        vehiculo not in memory.vehiculos.listar(1), "Desaparece del listado activo"
    )
    verificar(
        cliente.get(f"/vehiculos/{vehiculo.id}/").status_code == 200,
        "Conserva el detalle en modo consulta",
    )

    rutas_escritura = (
        f"/vehiculos/{vehiculo.id}/editar/",
        f"/vehiculos/{vehiculo.id}/documentos/",
        f"/vehiculos/{vehiculo.id}/mantenimientos/nuevo/",
        f"/vehiculos/{vehiculo.id}/baja/",
    )
    verificar(
        all(cliente.get(ruta).status_code == 302 for ruta in rutas_escritura),
        "Bloquea todas las acciones de escritura por URL",
    )


# ---------------------------------------------------------------------------
# HU7, HU8 — Documentos
# ---------------------------------------------------------------------------


def probar_documentos() -> None:
    print("\nHU7, HU8 — Documentos legales")
    cliente = sesion_iniciada()
    vehiculo = memory.vehiculos.listar(1, placa_contiene="ABC123")[0]

    verificar(
        contiene(
            cliente.post(
                f"/vehiculos/{vehiculo.id}/documentos/",
                {"vencimiento_soat": "no-es-fecha", "vencimiento_tecnomecanica": ""},
            ),
            Mensajes.FECHA_INVALIDA,
        ),
        "Rechaza fechas inválidas",
    )
    verificar(
        cliente.post(
            f"/vehiculos/{vehiculo.id}/documentos/",
            {
                "vencimiento_soat": (HOY + timedelta(days=200)).isoformat(),
                "vencimiento_tecnomecanica": (HOY + timedelta(days=200)).isoformat(),
            },
        ).status_code == 302,
        "Guarda las fechas de vencimiento",
    )

    config = memory.configuracion.obtener()
    verificar(
        rules.estado_documento(HOY + timedelta(days=200), config) is EstadoDocumento.VIGENTE,
        "Clasifica como vigente un documento lejano",
    )
    verificar(
        rules.estado_documento(HOY + timedelta(days=10), config) is EstadoDocumento.POR_VENCER,
        "Clasifica como próximo a vencer dentro del umbral",
    )
    verificar(
        rules.estado_documento(AYER, config) is EstadoDocumento.VENCIDO,
        "Clasifica como vencido un documento pasado",
    )
    verificar(
        rules.estado_documento(None, config) is EstadoDocumento.SIN_REGISTRO,
        "Clasifica como sin registro cuando no hay fecha",
    )


# ---------------------------------------------------------------------------
# HU9, HU10 — Mantenimientos
# ---------------------------------------------------------------------------


def probar_mantenimientos() -> None:
    print("\nHU9, HU10 — Mantenimiento preventivo")
    cliente = sesion_iniciada()
    vehiculo = memory.vehiculos.listar(1, placa_contiene="ABC123")[0]
    base = f"/vehiculos/{vehiculo.id}/mantenimientos/"

    verificar(cliente.get(f"{base}nuevo/").status_code == 200, "Muestra el formulario")
    verificar(
        contiene(
            cliente.post(f"{base}nuevo/", {"tipo": "Frenos", "criterio": "fecha", "fecha_programada": AYER.isoformat()}),
            Mensajes.FECHA_PASADA,
        ),
        "Rechaza una fecha anterior a hoy",
    )
    verificar(
        contiene(
            cliente.post(f"{base}nuevo/", {"tipo": "Frenos", "criterio": "kilometraje", "kilometraje_objetivo": 1}),
            Mensajes.KM_OBJETIVO_INVALIDO,
        ),
        "Rechaza un objetivo menor al kilometraje actual",
    )

    respuesta = cliente.post(
        f"{base}nuevo/",
        {"tipo": "Cambio de filtro", "criterio": "fecha", "fecha_programada": MANANA.isoformat()},
    )
    verificar(respuesta.status_code == 302, "Programa un mantenimiento por fecha")

    creado = memory.mantenimientos.listar(vehiculo.id, cumplidos=False)[-1]
    verificar(creado.kilometraje_objetivo is None, "El criterio es excluyente")

    verificar(
        cliente.get(f"{base}{creado.id}/cumplir/").status_code == 405,
        "El cumplimiento solo acepta POST",
    )
    verificar(
        cliente.post(f"{base}{creado.id}/cumplir/").status_code == 302, "Marca como cumplido"
    )
    verificar(creado.cumplido and creado.fecha_cumplimiento == HOY, "Registra la fecha real")
    verificar(
        not servicio_mantenimientos.marcar_cumplido(creado, vehiculo),
        "El cumplimiento es irreversible",
    )


# ---------------------------------------------------------------------------
# HU14 — Kilometraje
# ---------------------------------------------------------------------------


def probar_kilometraje() -> None:
    print("\nHU14 — Kilometraje")
    cliente = sesion_iniciada()
    vehiculo = memory.vehiculos.listar(1, placa_contiene="ABC123")[0]
    actual = vehiculo.kilometraje_actual

    verificar(
        cliente.get(f"/kilometraje/?vehiculo={vehiculo.id}").status_code == 200,
        "Permite preseleccionar el vehículo",
    )
    verificar(
        contiene(
            cliente.post("/kilometraje/", {"vehiculo_id": str(vehiculo.id), "kilometraje": 1, "fecha_lectura": HOY.isoformat()}),
            Mensajes.KM_MENOR,
        ),
        "Rechaza un kilometraje menor al último",
    )
    verificar(
        contiene(
            cliente.post("/kilometraje/", {"vehiculo_id": str(vehiculo.id), "kilometraje": actual + 100, "fecha_lectura": MANANA.isoformat()}),
            Mensajes.FECHA_FUTURA,
        ),
        "Rechaza una fecha futura",
    )
    verificar(
        cliente.post("/kilometraje/", {"vehiculo_id": str(vehiculo.id), "kilometraje": actual + 500, "fecha_lectura": HOY.isoformat()}).status_code == 302,
        "Registra una lectura válida",
    )
    verificar(vehiculo.kilometraje_actual == actual + 500, "Sincroniza el vehículo")

    objetivo = vehiculo.kilometraje_actual - 10
    pendiente = servicio_mantenimientos.programar(
        vehiculo, {"tipo": "Correa", "criterio": "kilometraje", "kilometraje_objetivo": objetivo}
    )
    verificar(
        rules.estado_mantenimiento(pendiente, vehiculo.kilometraje_actual)
        is EstadoMantenimiento.ATRASADO,
        "El kilometraje reevalúa los mantenimientos",
    )


# ---------------------------------------------------------------------------
# HU11, HU12 — Alertas y panel
# ---------------------------------------------------------------------------


def probar_alertas_y_panel() -> None:
    print("\nHU11, HU12 — Alertas y panel")
    cliente = sesion_iniciada()

    verificar(cliente.get("/alertas/").status_code == 200, "Muestra la configuración")
    verificar(
        contiene(
            cliente.post("/alertas/", {"umbral_km": 500, "correo_notificaciones": "a@b.com"}),
            Mensajes.UMBRAL_REQUERIDO,
        ),
        "Exige al menos un umbral",
    )
    verificar(
        cliente.post("/alertas/", {"umbrales_dias": ["30", "15"], "umbral_km": 700, "correo_notificaciones": "avisos@empresa.com"}).status_code == 302,
        "Guarda la configuración",
    )

    config = memory.configuracion.obtener()
    verificar(config.umbral_mayor == 30, "El umbral mayor define la ventana de alerta")

    resumen = servicio_panel.construir_resumen(1)
    verificar(resumen.total == len(memory.vehiculos.listar(1)), "Los indicadores cubren la flota")


# ---------------------------------------------------------------------------
# Regresiones corregidas en la revisión de código
# ---------------------------------------------------------------------------


def probar_regresiones() -> None:
    print("\nRegresiones")
    cliente = sesion_iniciada()
    config = memory.configuracion.obtener()

    cliente.post("/vehiculos/nuevo/", datos_vehiculo(placa="SIN001"))
    nuevo = memory.vehiculos.listar(1, placa_contiene="SIN001")[0]
    verificar(
        rules.estado_documental(nuevo, config) is EstadoDocumento.SIN_REGISTRO,
        "Un vehículo sin documentos no se reporta como vigente",
    )

    resumen = servicio_panel.construir_resumen(1)
    verificar(resumen.sin_registro >= 1, "El panel cuenta los vehículos sin documentos")
    verificar(
        any(f.vehiculo.placa == "SIN001" for f in resumen.atencion),
        "El panel los lista como pendientes de completar",
    )

    referencia = memory.vehiculos.listar(1, placa_contiene="ABC123")[0]
    for mantenimiento in memory.mantenimientos.listar(referencia.id, cumplidos=False):
        mantenimiento.cumplido = True

    servicio_mantenimientos.programar(
        referencia, {"tipo": "Aceite", "criterio": "fecha", "fecha_programada": HOY + timedelta(days=25)}
    )
    servicio_mantenimientos.programar(
        referencia,
        {"tipo": "Frenos", "criterio": "kilometraje", "kilometraje_objetivo": referencia.kilometraje_actual + 50},
    )
    pendientes = [p.mantenimiento for p in servicio_mantenimientos.pendientes(referencia)]
    verificar(
        "km" in rules.proximo_mantenimiento(pendientes, referencia, config),
        "La urgencia compara días y kilómetros normalizados",
    )

    verificar(filtro_km(None) == "—", "El filtro de kilometraje no imprime None")
    verificar(filtro_km(46250) == "46.250", "El filtro aplica separador de miles")

    ajeno = servicio_vehiculos.VehiculoNoEncontrado
    try:
        servicio_vehiculos.obtener(9999, 1)
        aislado = False
    except ajeno:
        aislado = True
    verificar(aislado, "El servicio aísla las flotas entre administradores")


# ---------------------------------------------------------------------------
# Ejecución
# ---------------------------------------------------------------------------


def main() -> int:
    print("alVolante — Pruebas del MVP")
    for prueba in (
        probar_autenticacion,
        probar_vehiculos,
        probar_documentos,
        probar_mantenimientos,
        probar_kilometraje,
        probar_alertas_y_panel,
        probar_baja,
        probar_perfil,
        probar_regresiones,
    ):
        prueba()

    print("\n" + "-" * 60)
    if _fallos:
        print(f"{len(_fallos)} prueba(s) fallida(s):")
        for fallo in _fallos:
            print(f"  - {fallo}")
        return 1

    print("Todas las pruebas pasaron.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
