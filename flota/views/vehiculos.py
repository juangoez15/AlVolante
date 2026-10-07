"""Vistas de gestión de vehículos y sus documentos (HU3 a HU8, HU15)."""

from __future__ import annotations

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from flota.constants import Mensajes
from flota.decorators import bloquear_si_inactivo, login_requerido, traducir_no_encontrado
from flota.domain import rules
from flota.forms import DocumentosForm, VehiculoForm
from flota.repositories.orm import configuracion as repo_configuracion
from flota.services import kilometraje as servicio_kilometraje
from flota.services import mantenimientos as servicio_mantenimientos
from flota.services import vehiculos as servicio


@login_requerido
def listar(request: HttpRequest) -> HttpResponse:
    """Listado de la flota activa con búsqueda por placa (HU4)."""
    buscar = request.GET.get("q", "")
    return render(
        request,
        "flota/vehiculos.html",
        {"filas": servicio.listar(request.usuario.id, buscar), "buscar": buscar},
    )


@login_requerido
def crear(request: HttpRequest) -> HttpResponse:
    """Registro de un vehículo nuevo (HU3)."""
    formulario = VehiculoForm(request.POST or None, usuario_id=request.usuario.id)

    if request.method == "POST" and formulario.is_valid():
        vehiculo = servicio.registrar(request.usuario.id, formulario.cleaned_data)
        messages.success(request, Mensajes.VEHICULO_CREADO)
        return redirect("vehiculo_detalle", vehiculo_id=vehiculo.id)

    contexto = {"form": formulario, "titulo": "Registrar vehículo", "es_creacion": True}
    return render(request, "flota/vehiculo_form.html", contexto)


@login_requerido
@traducir_no_encontrado
def editar(request: HttpRequest, vehiculo_id: int) -> HttpResponse:
    """Actualización de los datos del vehículo (HU5)."""
    vehiculo = servicio.obtener(vehiculo_id, request.usuario.id)
    if bloquear_si_inactivo(request, vehiculo):
        return redirect("vehiculo_detalle", vehiculo_id=vehiculo.id)

    formulario = VehiculoForm(
        request.POST or None,
        initial=servicio.datos_editables(vehiculo),
        usuario_id=request.usuario.id,
        vehiculo_id=vehiculo.id,
    )

    if request.method == "POST" and formulario.is_valid():
        servicio.actualizar(vehiculo, formulario.cleaned_data)
        messages.success(request, Mensajes.VEHICULO_ACTUALIZADO)
        return redirect("vehiculo_detalle", vehiculo_id=vehiculo.id)

    contexto = {
        "form": formulario,
        "titulo": "Editar vehículo",
        "es_creacion": False,
        "vehiculo": vehiculo,
    }
    return render(request, "flota/vehiculo_form.html", contexto)


@login_requerido
@traducir_no_encontrado
def dar_de_baja(request: HttpRequest, vehiculo_id: int) -> HttpResponse:
    """Baja lógica con confirmación previa (HU6)."""
    vehiculo = servicio.obtener(vehiculo_id, request.usuario.id)
    if bloquear_si_inactivo(request, vehiculo):
        return redirect("vehiculo_detalle", vehiculo_id=vehiculo.id)

    if request.method == "POST":
        servicio.dar_de_baja(vehiculo)
        messages.success(request, f"El vehículo {vehiculo.placa} fue dado de baja")
        return redirect("vehiculos")

    return render(request, "flota/vehiculo_baja.html", {"vehiculo": vehiculo})


@login_requerido
@traducir_no_encontrado
def detalle(request: HttpRequest, vehiculo_id: int) -> HttpResponse:
    """
    Ficha completa del vehículo (HU15).

    Consolida datos generales, estado documental (HU8), mantenimientos
    pendientes y cumplidos (HU9, HU10) y últimas lecturas (HU14).
    """
    vehiculo = servicio.obtener(vehiculo_id, request.usuario.id)
    config = repo_configuracion.obtener()

    contexto = {
        "vehiculo": vehiculo,
        "estado_soat": rules.estado_soat(vehiculo, config),
        "estado_tecnomecanica": rules.estado_tecnomecanica(vehiculo, config),
        "mantenimientos": servicio_mantenimientos.pendientes(vehiculo),
        "historial": servicio_mantenimientos.historial(vehiculo),
        "lecturas": servicio_kilometraje.ultimas_lecturas(vehiculo),
    }
    return render(request, "flota/vehiculo_detalle.html", contexto)


@login_requerido
@traducir_no_encontrado
def documentos(request: HttpRequest, vehiculo_id: int) -> HttpResponse:
    """Registro y actualización de SOAT y Tecnomecánica (HU7)."""
    vehiculo = servicio.obtener(vehiculo_id, request.usuario.id)
    if bloquear_si_inactivo(request, vehiculo):
        return redirect("vehiculo_detalle", vehiculo_id=vehiculo.id)

    inicial = {
        "vencimiento_soat": vehiculo.vencimiento_soat,
        "vencimiento_tecnomecanica": vehiculo.vencimiento_tecnomecanica,
    }
    formulario = DocumentosForm(request.POST or None, initial=inicial)

    if request.method == "POST" and formulario.is_valid():
        servicio.actualizar_documentos(
            vehiculo,
            formulario.cleaned_data["vencimiento_soat"],
            formulario.cleaned_data["vencimiento_tecnomecanica"],
        )
        messages.success(request, Mensajes.DOCUMENTOS_ACTUALIZADOS)
        return redirect("vehiculo_detalle", vehiculo_id=vehiculo.id)

    return render(request, "flota/documentos.html", {"form": formulario, "vehiculo": vehiculo}) 