from __future__ import annotations

from datetime import date
from flota.domain.entities import (
    Configuracion,
    LecturaKilometraje,
    Mantenimiento,
    Usuario,
    Vehiculo,
)
from flota.models import (
    UsuarioModel,
    VehiculoModel,
    MantenimientoModel,
    LecturaKilometrajeModel,
    ConfiguracionModel,
)

class UsuarioRepository:
    """Cuentas de administrador de flota conectadas a PostgreSQL."""

    def listar(self) -> list[Usuario]:
        return [self._a_entidad(u) for u in UsuarioModel.objects.all()]

    def obtener(self, usuario_id: int) -> Usuario | None:
        u = UsuarioModel.objects.filter(id=usuario_id).first()
        return self._a_entidad(u) if u else None

    def por_correo(self, correo: str) -> Usuario | None:
        correo = correo.strip().lower()
        u = UsuarioModel.objects.filter(correo__iexact=correo).first()
        return self._a_entidad(u) if u else None

    def correo_en_uso(self, correo: str, excluir_id: int | None = None) -> bool:
        correo = correo.strip().lower()
        qs = UsuarioModel.objects.filter(correo__iexact=correo)
        if excluir_id:
            qs = qs.exclude(id=excluir_id)
        return qs.exists()

    def crear(self, nombre: str, correo: str, password: str) -> Usuario:
        u = UsuarioModel.objects.create(nombre=nombre, correo=correo.lower(), password=password)
        return self._a_entidad(u)

    def actualizar(self, usuario: Usuario, avatar_file=None) -> Usuario | None:
        """Actualiza los datos del usuario, permitiendo opcionalmente cambiar la imagen de avatar."""
        u = UsuarioModel.objects.filter(id=usuario.id).first()
        if not u:
            return None
        
        u.nombre = usuario.nombre
        u.correo = usuario.correo.lower()
        if usuario.password:
            u.password = usuario.password
            
        if avatar_file:
            u.avatar = avatar_file
            
        u.save()
        return self._a_entidad(u)

    def _a_entidad(self, u: UsuarioModel) -> Usuario:
        avatar_url = None
        if u.avatar:
            # Oñemboguejy pe try...except ani hag̃ua oñokañy pe error ha ohechauka porã haguã
            avatar_url = u.avatar.url

        return Usuario(
            id=u.id, 
            nombre=u.nombre, 
            correo=u.correo, 
            password=u.password, 
            avatar=avatar_url
        )


class VehiculoRepository:
    """Vehículos gestionados mediante PostgreSQL ORM."""

    def listar(
        self,
        usuario_id: int,
        *,
        solo_activos: bool = True,
        placa_contiene: str = "",
    ) -> list[Vehiculo]:
        qs = VehiculoModel.objects.filter(usuario_id=usuario_id)
        if solo_activos:
            qs = qs.filter(activo=True)
        if placa_contiene:
            qs = qs.filter(placa__icontains=placa_contiene.strip())
        
        qs = qs.order_by('placa')
        return [self._a_entidad(v) for v in qs]

    def obtener(self, vehiculo_id: int, usuario_id: int) -> Vehiculo | None:
        v = VehiculoModel.objects.filter(id=vehiculo_id, usuario_id=usuario_id).first()
        return self._a_entidad(v) if v else None

    def placa_en_uso(self, placa: str, usuario_id: int, excluir_id: int | None = None) -> bool:
        placa = placa.strip().upper()
        qs = VehiculoModel.objects.filter(placa__iexact=placa, usuario_id=usuario_id)
        if excluir_id:
            qs = qs.exclude(id=excluir_id)
        return qs.exists()

    def agregar(self, vehiculo: Vehiculo) -> Vehiculo:
        v = VehiculoModel.objects.create(
            usuario_id=vehiculo.usuario_id,
            placa=vehiculo.placa.upper(),
            tipo=vehiculo.tipo,
            marca=vehiculo.marca,
            modelo=vehiculo.modelo,
            anio=vehiculo.anio,
            kilometraje_actual=vehiculo.kilometraje_actual,
            vencimiento_soat=vehiculo.vencimiento_soat,
            vencimiento_tecnomecanica=vehiculo.vencimiento_tecnomecanica,
            fecha_ultima_lectura=vehiculo.fecha_ultima_lectura,
            activo=vehiculo.activo,
        )
        vehiculo.id = v.id
        return vehiculo

    def actualizar(self, vehiculo: Vehiculo) -> Vehiculo | None:
        """Actualiza un vehículo existente en la base de datos."""
        v = VehiculoModel.objects.filter(id=vehiculo.id, usuario_id=vehiculo.usuario_id).first()
        if not v:
            return None
        
        v.placa = vehiculo.placa.upper()
        v.tipo = vehiculo.tipo
        v.marca = vehiculo.marca
        v.modelo = vehiculo.modelo
        v.anio = vehiculo.anio
        v.kilometraje_actual = vehiculo.kilometraje_actual
        v.vencimiento_soat = vehiculo.vencimiento_soat
        v.vencimiento_tecnomecanica = vehiculo.vencimiento_tecnomecanica
        v.fecha_ultima_lectura = vehiculo.fecha_ultima_lectura
        v.activo = vehiculo.activo
        v.save()
        
        return self._a_entidad(v)

    def _a_entidad(self, v: VehiculoModel) -> Vehiculo:
        return Vehiculo(
            id=v.id,
            usuario_id=v.usuario_id,
            placa=v.placa,
            tipo=v.tipo,
            marca=v.marca,
            modelo=v.modelo,
            anio=v.anio,
            kilometraje_actual=v.kilometraje_actual,
            vencimiento_soat=v.vencimiento_soat,
            vencimiento_tecnomecanica=v.vencimiento_tecnomecanica,
            fecha_ultima_lectura=v.fecha_ultima_lectura,
            activo=v.activo,
        )


class MantenimientoRepository:
    """Mantenimientos preventivos en base de datos."""

    def listar(self, vehiculo_id: int, *, cumplidos: bool | None = None):
        qs = MantenimientoModel.objects.filter(vehiculo_id=vehiculo_id)
        if cumplidos is not None:
            qs = qs.filter(cumplido=cumplidos)
        qs = qs.order_by('id')
        return [self._a_entidad(m) for m in qs]

    def obtener(self, mantenimiento_id: int, vehiculo_id: int) -> Mantenimiento | None:
        m = MantenimientoModel.objects.filter(id=mantenimiento_id, vehiculo_id=vehiculo_id).first()
        return self._a_entidad(m) if m else None

    def agregar(self, mantenimiento: Mantenimiento) -> Mantenimiento:
        m = MantenimientoModel.objects.create(
            vehiculo_id=mantenimiento.vehiculo_id,
            tipo=mantenimiento.tipo,
            criterio=mantenimiento.criterio,
            fecha_programada=mantenimiento.fecha_programada,
            kilometraje_objetivo=mantenimiento.kilometraje_objetivo,
            cumplido=mantenimiento.cumplido,
            fecha_cumplimiento=mantenimiento.fecha_cumplimiento,
            kilometraje_cumplimiento=mantenimiento.kilometraje_cumplimiento,
        )
        mantenimiento.id = m.id
        return mantenimiento

    def actualizar(self, mantenimiento: Mantenimiento) -> Mantenimiento | None:
        """Actualiza un mantenimiento existente (ej. marcar como cumplido)."""
        m = MantenimientoModel.objects.filter(id=mantenimiento.id, vehiculo_id=mantenimiento.vehiculo_id).first()
        if not m:
            return None
        
        m.tipo = mantenimiento.tipo
        m.criterio = mantenimiento.criterio
        m.fecha_programada = mantenimiento.fecha_programada
        m.kilometraje_objetivo = mantenimiento.kilometraje_objetivo
        m.cumplido = mantenimiento.cumplido
        m.fecha_cumplimiento = mantenimiento.fecha_cumplimiento
        m.kilometraje_cumplimiento = mantenimiento.kilometraje_cumplimiento
        m.save()
        
        return self._a_entidad(m)

    def _a_entidad(self, m: MantenimientoModel) -> Mantenimiento:
        return Mantenimiento(
            id=m.id,
            vehiculo_id=m.vehiculo_id,
            tipo=m.tipo,
            criterio=m.criterio,
            fecha_programada=m.fecha_programada,
            kilometraje_objetivo=m.kilometraje_objetivo,
            cumplido=m.cumplido,
            fecha_cumplimiento=m.fecha_cumplimiento,
            kilometraje_cumplimiento=m.kilometraje_cumplimiento,
        )


class LecturaRepository:
    """Histórico de odómetro en base de datos."""

    def historico(self, vehiculo_id: int) -> list[LecturaKilometraje]:
        qs = LecturaKilometrajeModel.objects.filter(vehiculo_id=vehiculo_id).order_by('-fecha_lectura', '-id')
        return [self._a_entidad(l) for l in qs]

    def ultima(self, vehiculo_id: int) -> LecturaKilometraje | None:
        l = LecturaKilometrajeModel.objects.filter(vehiculo_id=vehiculo_id).order_by('-fecha_lectura', '-id').first()
        return self._a_entidad(l) if l else None

    def agregar(self, vehiculo_id: int, kilometraje: int, fecha_lectura: date) -> LecturaKilometraje:
        l = LecturaKilometrajeModel.objects.create(
            vehiculo_id=vehiculo_id, kilometraje=kilometraje, fecha_lectura=fecha_lectura
        )
        return self._a_entidad(l)

    def _a_entidad(self, l: LecturaKilometrajeModel) -> LecturaKilometraje:
        return LecturaKilometraje(
            id=l.id, 
            vehiculo_id=l.vehiculo_id, 
            kilometraje=l.kilometraje, 
            fecha_lectura=l.fecha_lectura
        )


class ConfiguracionRepository:
    """Configuración única del sistema en base de datos."""

    def obtener(self) -> Configuracion:
        c, _ = ConfiguracionModel.objects.get_or_create(id=1)
        import json
        try:
            umbrales = json.loads(c.umbrales_dias_json)
        except Exception:
            umbrales = [30, 15, 7]
            
        return Configuracion(
            umbrales_dias=umbrales,
            umbral_km=c.umbral_km,
            correo_notificaciones=c.correo_notificaciones,
        )

    def guardar(
        self, *, umbrales_dias: list[int], umbral_km: int, correo_notificaciones: str
    ) -> Configuracion:
        import json
        c, _ = ConfiguracionModel.objects.get_or_create(id=1)
        c.umbrales_dias_json = json.dumps(sorted(umbrales_dias, reverse=True))
        c.umbral_km = umbral_km
        c.correo_notificaciones = correo_notificaciones
        c.save()
        return self.obtener()


usuarios = UsuarioRepository()
vehiculos = VehiculoRepository()
mantenimientos = MantenimientoRepository()
lecturas = LecturaRepository()
configuracion = ConfiguracionRepository()