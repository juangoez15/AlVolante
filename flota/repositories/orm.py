from __future__ import annotations

import json

from flota.domain.entities import Usuario, Configuracion, Vehiculo, Mantenimiento, LecturaKilometraje
from flota.models import (
    UsuarioModel,
    ConfiguracionModel,
    VehiculoModel,
    MantenimientoModel,
    LecturaKilometrajeModel,
)


class UsuarioRepository:
    """Repositorio ORM para la entidad Usuario."""

    def obtener_por_id(self, usuario_id: int) -> Usuario | None:
        try:
            u = UsuarioModel.objects.get(pk=usuario_id)
            return self._a_entidad(u)
        except UsuarioModel.DoesNotExist:
            return None

    def obtener(self, usuario_id: int) -> Usuario | None:
        return self.obtener_por_id(usuario_id)

    def listar(self) -> list[Usuario]:
        return [self._a_entidad(u) for u in UsuarioModel.objects.all()]

    def obtener_unico(self) -> Usuario | None:
        u = UsuarioModel.objects.first()
        return self._a_entidad(u) if u else None

    def por_correo(self, correo: str) -> Usuario | None:
        """Busca un usuario por su correo electrónico (ignorando mayúsculas)."""
        if not correo:
            return None
        correo = correo.strip().lower()
        u = UsuarioModel.objects.filter(correo__iexact=correo).first()
        return self._a_entidad(u) if u else None

    def correo_en_uso(self, correo: str, excluir_id: int | None = None) -> bool:
        """Verifica si un correo ya está registrado por otro usuario."""
        if not correo:
            return False
        correo = correo.strip().lower()
        qs = UsuarioModel.objects.filter(correo__iexact=correo)
        if excluir_id:
            qs = qs.exclude(id=excluir_id)
        return qs.exists()

    def guardar(self, usuario: Usuario) -> Usuario:
        u, creado = UsuarioModel.objects.update_or_create(
            id=usuario.id if usuario.id else 1,
            defaults={
                "nombre": usuario.nombre,
                "correo": usuario.correo,
                "password": usuario.password,
            },
        )
        return self._a_entidad(u)

    def actualizar(self, usuario: Usuario, avatar_file=None) -> Usuario:
        """Actualiza los datos del usuario incluyendo de forma segura el archivo del avatar."""
        u = UsuarioModel.objects.filter(pk=usuario.id if usuario.id else 1).first()
        if not u:
            u = UsuarioModel.objects.first()

        if u:
            u.nombre = usuario.nombre
            u.correo = usuario.correo
            if usuario.password:
                u.password = usuario.password
            
            # Si se envió un archivo de avatar nuevo, se asigna directamente al campo FileField de Django
            if avatar_file:
                u.avatar = avatar_file

            u.save()
            return self._a_entidad(u)
        
        return self.guardar(usuario)

    def _a_entidad(self, u: UsuarioModel) -> Usuario:
        avatar_url = None
        if u and u.avatar:
            try:
                # Intentamos extraer la URL desde el campo FileField de Django
                if hasattr(u.avatar, 'url') and u.avatar.url:
                    avatar_url = u.avatar.url
                else:
                    ruta = str(u.avatar).strip()
                    if ruta and ruta != 'None' and ruta != '':
                        avatar_url = ruta if ruta.startswith("/") or ruta.startswith("http") else f"/media/{ruta}"
            except Exception:
                avatar_url = None

        return Usuario(
            id=u.id if u else 1,
            nombre=u.nombre if u else "",
            correo=u.correo if u else "",
            password=u.password if u else "",
            avatar=avatar_url,
        )

class ConfiguracionRepository:
    """Repositorio ORM para la entidad Configuracion."""

    def obtener(self) -> Configuracion:
        c, creado = ConfiguracionModel.objects.get_or_create(pk=1)
        return self._a_entidad(c)

    def guardar(
        self, *, umbrales_dias: list[int], umbral_km: int, correo_notificaciones: str
    ) -> Configuracion:
        c, creado = ConfiguracionModel.objects.update_or_create(
            pk=1,
            defaults={
                "umbrales_dias_json": json.dumps(sorted(umbrales_dias, reverse=True)),
                "umbral_km": umbral_km,
                "correo_notificaciones": correo_notificaciones,
            },
        )
        return self._a_entidad(c)

    def _a_entidad(self, c: ConfiguracionModel) -> Configuracion:
        try:
            umbrales = [int(d) for d in json.loads(c.umbrales_dias_json)]
        except (ValueError, TypeError):
            umbrales = [30, 15, 7]

        return Configuracion(
            umbrales_dias=umbrales,
            umbral_km=c.umbral_km,
            correo_notificaciones=c.correo_notificaciones,
        )


class VehiculoRepository:
    """Repositorio ORM para la entidad Vehiculo."""

    def obtener_todos(self, usuario_id: int) -> list[Vehiculo]:
        qs = VehiculoModel.objects.filter(usuario_id=usuario_id)
        return [self._a_entidad(v) for v in qs]

    def listar(
        self,
        usuario_id: int | None = None,
        *,
        solo_activos: bool = True,
        placa_contiene: str = "",
    ) -> list[Vehiculo]:
        """Lista la flota de un usuario; filtra activos y por placa (HU4, HU12)."""
        qs = VehiculoModel.objects.all()
        if usuario_id is not None:
            qs = qs.filter(usuario_id=usuario_id)
        if solo_activos:
            qs = qs.filter(activo=True)
        if placa_contiene:
            qs = qs.filter(placa__icontains=placa_contiene.strip())
        return [self._a_entidad(v) for v in qs.order_by("placa")]

    def obtener(self, vehiculo_id: int, usuario_id: int) -> Vehiculo | None:
        """Filtra por usuario para aislar flotas incluso al entrar por URL."""
        v = VehiculoModel.objects.filter(pk=vehiculo_id, usuario_id=usuario_id).first()
        return self._a_entidad(v) if v else None

    def placa_en_uso(self, placa: str, usuario_id: int, excluir_id: int | None = None) -> bool:
        qs = VehiculoModel.objects.filter(placa__iexact=placa.strip(), activo=True)
        if excluir_id:
            qs = qs.exclude(pk=excluir_id)
        return qs.exists()

    def agregar(self, vehiculo: Vehiculo) -> Vehiculo:
        v = VehiculoModel.objects.create(
            usuario_id=vehiculo.usuario_id,
            placa=vehiculo.placa,
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

    def actualizar(self, vehiculo: Vehiculo) -> Vehiculo:
        return self.guardar(vehiculo)

    def obtener_por_id(self, vehiculo_id: int) -> Vehiculo | None:
        try:
            v = VehiculoModel.objects.get(pk=vehiculo_id)
            return self._a_entidad(v)
        except VehiculoModel.DoesNotExist:
            return None

    def guardar(self, vehiculo: Vehiculo) -> Vehiculo:
        v, creado = VehiculoModel.objects.update_or_create(
            id=vehiculo.id if vehiculo.id else None,
            defaults={
                "usuario_id": vehiculo.usuario_id,
                "placa": vehiculo.placa,
                "tipo": vehiculo.tipo,
                "marca": vehiculo.marca,
                "modelo": vehiculo.modelo,
                "anio": vehiculo.anio,
                "kilometraje_actual": vehiculo.kilometraje_actual,
                "vencimiento_soat": vehiculo.vencimiento_soat,
                "vencimiento_tecnomecanica": vehiculo.vencimiento_tecnomecanica,
                "fecha_ultima_lectura": vehiculo.fecha_ultima_lectura,
                "activo": vehiculo.activo,
            },
        )
        vehiculo.id = v.id
        return vehiculo

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
    """Repositorio ORM para la entidad Mantenimiento."""

    def obtener_por_vehiculo(self, vehiculo_id: int) -> list[Mantenimiento]:
        qs = MantenimientoModel.objects.filter(vehiculo_id=vehiculo_id)
        return [self._a_entidad(m) for m in qs]

    def listar(self, vehiculo_id: int, *, cumplidos: bool | None = None) -> list[Mantenimiento]:
        qs = MantenimientoModel.objects.filter(vehiculo_id=vehiculo_id)
        if cumplidos is not None:
            qs = qs.filter(cumplido=cumplidos)
        return [self._a_entidad(m) for m in qs.order_by("id")]

    def obtener(self, mantenimiento_id: int, vehiculo_id: int) -> Mantenimiento | None:
        m = MantenimientoModel.objects.filter(pk=mantenimiento_id, vehiculo_id=vehiculo_id).first()
        return self._a_entidad(m) if m else None

    def agregar(self, mantenimiento: Mantenimiento) -> Mantenimiento:
        return self.guardar(mantenimiento)

    def obtener_por_id(self, mantenimiento_id: int) -> Mantenimiento | None:
        try:
            m = MantenimientoModel.objects.get(pk=mantenimiento_id)
            return self._a_entidad(m)
        except MantenimientoModel.DoesNotExist:
            return None

    def guardar(self, mantenimiento: Mantenimiento) -> Mantenimiento:
        m, creado = MantenimientoModel.objects.update_or_create(
            id=mantenimiento.id if mantenimiento.id else None,
            defaults={
                "vehiculo_id": mantenimiento.vehiculo_id,
                "tipo": mantenimiento.tipo,
                "criterio": mantenimiento.criterio,
                "fecha_programada": mantenimiento.fecha_programada,
                "kilometraje_objetivo": mantenimiento.kilometraje_objetivo,
                "cumplido": mantenimiento.cumplido,
                "fecha_cumplimiento": mantenimiento.fecha_cumplimiento,
                "kilometraje_cumplimiento": mantenimiento.kilometraje_cumplimiento,
            },
        )
        mantenimiento.id = m.id
        return mantenimiento

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


class LecturaKilometrajeRepository:
    """Repositorio ORM para la entidad LecturaKilometraje."""

    def obtener_por_vehiculo(self, vehiculo_id: int) -> list[LecturaKilometraje]:
        qs = LecturaKilometrajeModel.objects.filter(vehiculo_id=vehiculo_id).order_by("-fecha_lectura")
        return [self._a_entidad(l) for l in qs]

    def historico(self, vehiculo_id: int) -> list[LecturaKilometraje]:
        """Lecturas de la más reciente a la más antigua."""
        qs = LecturaKilometrajeModel.objects.filter(vehiculo_id=vehiculo_id).order_by(
            "-fecha_lectura", "-id"
        )
        return [self._a_entidad(l) for l in qs]

    def ultima(self, vehiculo_id: int) -> LecturaKilometraje | None:
        historico = self.historico(vehiculo_id)
        return historico[0] if historico else None

    def agregar(self, vehiculo_id: int, kilometraje: int, fecha_lectura) -> LecturaKilometraje:
        l = LecturaKilometrajeModel.objects.create(
            vehiculo_id=vehiculo_id, kilometraje=kilometraje, fecha_lectura=fecha_lectura
        )
        return self._a_entidad(l)

    def guardar(self, lectura: LecturaKilometraje) -> LecturaKilometraje:
        l, creado = LecturaKilometrajeModel.objects.update_or_create(
            id=lectura.id if lectura.id else None,
            defaults={
                "vehiculo_id": lectura.vehiculo_id,
                "kilometraje": lectura.kilometraje,
                "fecha_lectura": lectura.fecha_lectura,
            },
        )
        lectura.id = l.id
        return lectura

    def _a_entidad(self, l: LecturaKilometrajeModel) -> LecturaKilometraje:
        return LecturaKilometraje(
            id=l.id,
            vehiculo_id=l.vehiculo_id,
            kilometraje=l.kilometraje,
            fecha_lectura=l.fecha_lectura,
        )


# Instancias globales exportadas para el resto de la aplicación
usuarios = UsuarioRepository()
configuracion = ConfiguracionRepository()
vehiculos = VehiculoRepository()
mantenimientos = MantenimientoRepository()
lecturas = LecturaKilometrajeRepository()