"""Rutas de alVolante. Cada ruta corresponde a una historia de usuario."""

from django.urls import path

from flota import views

urlpatterns = [
    # HU1, HU2 — Autenticación
    path("", views.login, name="login"),
    path("salir/", views.logout, name="logout"),
    # HU12 — Panel del administrador
    path("panel/", views.panel, name="panel"),
    # HU3 a HU6, HU15 — Vehículos
    path("vehiculos/", views.listar, name="vehiculos"),
    path("vehiculos/nuevo/", views.crear, name="vehiculo_crear"),
    path("vehiculos/<int:vehiculo_id>/", views.detalle, name="vehiculo_detalle"),
    path("vehiculos/<int:vehiculo_id>/editar/", views.editar, name="vehiculo_editar"),
    path("vehiculos/<int:vehiculo_id>/baja/", views.dar_de_baja, name="vehiculo_baja"),
    path("vehiculos/<int:vehiculo_id>/reactivar/", views.reactivar, name="vehiculo_reactivar"),  # <--- Ruta de reactivación añadida
    # HU7, HU8 — Documentos legales
    path("vehiculos/<int:vehiculo_id>/documentos/", views.documentos, name="documentos"),
    # HU9, HU10 — Mantenimiento preventivo
    path(
        "vehiculos/<int:vehiculo_id>/mantenimientos/nuevo/",
        views.programar,
        name="mantenimiento_crear",
    ),
    path(
        "vehiculos/<int:vehiculo_id>/mantenimientos/<int:mantenimiento_id>/cumplir/",
        views.marcar_cumplido,
        name="mantenimiento_cumplir",
    ),
    # HU14 — Kilometraje
    path("kilometraje/", views.registrar_kilometraje, name="kilometraje"),
    # HU11 — Alertas automáticas
    path("alertas/", views.alertas, name="alertas"),
    # HU13 — Perfil
    path("perfil/", views.perfil, name="perfil"),
]