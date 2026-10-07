from django.db import models
from flota.constants import CriterioMantenimiento, TipoVehiculo

class UsuarioModel(models.Model):
    nombre = models.CharField(max_length=150)
    correo = models.EmailField(unique=True)
    password = models.CharField(max_length=255) # Hash o texto plano según use tu auth actual
    avatar = models.ImageField(upload_to='perfiles/', null=True, blank=True)  # <-- Añadido

    class Meta:
        db_table = 'flota_usuario'

class VehiculoModel(models.Model):
    usuario = models.ForeignKey(UsuarioModel, on_delete=models.CASCADE, related_name='vehiculos')
    placa = models.CharField(max_length=10, unique=True)
    tipo = models.CharField(max_length=50, choices=[(t.value, t.name) for t in TipoVehiculo])
    marca = models.CharField(max_length=100)
    modelo = models.CharField(max_length=100)
    anio = models.IntegerField()
    kilometraje_actual = models.IntegerField(default=0)
    vencimiento_soat = models.DateField(null=True, blank=True)
    vencimiento_tecnomecanica = models.DateField(null=True, blank=True)
    fecha_ultima_lectura = models.DateField(null=True, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = 'flota_vehiculo'

class MantenimientoModel(models.Model):
    vehiculo = models.ForeignKey(VehiculoModel, on_delete=models.CASCADE, related_name='mantenimientos')
    tipo = models.CharField(max_length=150)
    criterio = models.CharField(max_length=50, choices=[(c.value, c.name) for c in CriterioMantenimiento])
    fecha_programada = models.DateField(null=True, blank=True)
    kilometraje_objetivo = models.IntegerField(null=True, blank=True)
    cumplido = models.BooleanField(default=False)
    fecha_cumplimiento = models.DateField(null=True, blank=True)
    kilometraje_cumplimiento = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'flota_mantenimiento'

class LecturaKilometrajeModel(models.Model):
    vehiculo = models.ForeignKey(VehiculoModel, on_delete=models.CASCADE, related_name='lecturas')
    kilometraje = models.IntegerField()
    fecha_lectura = models.DateField()

    class Meta:
        db_table = 'flota_lectura_kilometraje'

class ConfiguracionModel(models.Model):
    # Al ser única, guardamos las listas serializadas o estructuradas
    umbrales_dias_json = models.CharField(max_length=100, default="[30, 15, 7]")
    umbral_km = models.IntegerField(default=1000)
    correo_notificaciones = models.EmailField(default="alertas@alvolante.com")

    class Meta:
        db_table = 'flota_configuracion'