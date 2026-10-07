# alVolante — MVP web (Python + Django)

Plataforma de gestión y control del mantenimiento preventivo y la vigencia
documental de flotas de vehículos. Proyecto **Proy-2026-001**.

Implementa las 15 historias de usuario con la arquitectura de la propuesta:
cliente-servidor en tres capas, patrón **MVT**, Django + Django Templates +
HTML5/CSS3 + Bootstrap 5.

## Estado: sin base de datos

Esta etapa no incluye PostgreSQL, SQLite, modelos ni migraciones. La
persistencia vive en memoria, en `flota/repositories/memory.py`.

- Los datos se reinician con el servidor y se re-siembran con la flota de demo.
- La sesión usa cookies firmadas, no tabla de sesiones.
- La autenticación es propia (`flota/auth.py`), no `django.contrib.auth`.
- **No ejecute `migrate` ni `createsuperuser`**: fallarán, y es lo esperado.

## Ejecutar

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py runserver
```

Abra http://127.0.0.1:8000/ e ingrese con:

```
Correo:     administrador@empresa.com
Contraseña: alvolante2026
```

```bash
python tests.py                             # pruebas de las 15 HU
python manage.py enviar_alertas --dry-run   # alertas en consola
```

## Arquitectura

Las dependencias van en una sola dirección; ninguna capa conoce a la que está
por encima:

```
Plantillas  →  Vistas  →  Servicios  →  Repositorios
                   ↘         ↓              ↓
                     Formularios  →      Dominio
```

| Capa | Responsabilidad | Ubicación |
|------|-----------------|-----------|
| **Dominio** | Entidades y reglas puras, sin Django | `flota/domain/` |
| **Repositorios** | Acceso a datos; única capa que cambia con PostgreSQL | `flota/repositories/` |
| **Servicios** | Casos de uso que orquestan dominio y repositorios | `flota/services/` |
| **Formularios** | Validación de entrada y mensajes de los criterios | `flota/forms/` |
| **Vistas** | HTTP, sesión y selección de plantilla | `flota/views/` |
| **Plantillas** | Presentación | `flota/templates/flota/` |

Migrar a PostgreSQL consiste en reimplementar las clases de
`repositories/memory.py` sobre el ORM. Dominio, servicios, vistas y plantillas
no cambian, porque nunca tocan las estructuras de almacenamiento.

## Estructura

```
alvolante/
├── manage.py
├── requirements.txt
├── tests.py                        # pruebas de las 15 HU y regresiones
├── config/                         # settings, urls, wsgi
└── flota/
    ├── constants.py                # estados, umbrales y mensajes
    ├── auth.py                     # sesión sin base de datos
    ├── decorators.py               # login, 404 y bloqueo de inactivos
    ├── urls.py
    ├── domain/
    │   ├── entities.py             # Vehiculo, Mantenimiento, Usuario…
    │   └── rules.py                # estados, urgencia, próximo mantenimiento
    ├── repositories/
    │   ├── memory.py               # repositorios en memoria
    │   └── seed.py                 # flota de demostración
    ├── services/                   # vehiculos, mantenimientos, kilometraje…
    ├── forms/                      # base, cuentas, vehiculos, configuracion…
    ├── views/                      # cuentas, panel, vehiculos, kilometraje…
    ├── templatetags/flota_extras.py
    ├── management/commands/enviar_alertas.py
    ├── static/flota/alvolante.css
    └── templates/flota/
        ├── partials/               # campo, mensajes, título, acciones
        └── *.html
```

## Mapa historia de usuario → código

| HU | Historia | Ruta | Vista |
|----|----------|------|-------|
| HU1 | Iniciar sesión | `/` | `views.cuentas.login` |
| HU2 | Cerrar sesión | `/salir/` | `views.cuentas.logout` |
| HU3 | Registrar vehículo | `/vehiculos/nuevo/` | `views.vehiculos.crear` |
| HU4 | Consultar vehículos | `/vehiculos/` | `views.vehiculos.listar` |
| HU5 | Actualizar vehículo | `/vehiculos/<id>/editar/` | `views.vehiculos.editar` |
| HU6 | Dar de baja vehículo | `/vehiculos/<id>/baja/` | `views.vehiculos.dar_de_baja` |
| HU7 | Registrar documentos | `/vehiculos/<id>/documentos/` | `views.vehiculos.documentos` |
| HU8 | Consultar estado documental | `/vehiculos/<id>/` | `views.vehiculos.detalle` |
| HU9 | Programar mantenimiento | `…/mantenimientos/nuevo/` | `views.mantenimientos.programar` |
| HU10 | Registrar cumplimiento | `…/mantenimientos/<id>/cumplir/` | `views.mantenimientos.marcar_cumplido` |
| HU11 | Configurar alertas | `/alertas/` | `views.configuracion.alertas` |
| HU12 | Panel del administrador | `/panel/` | `views.panel.panel` |
| HU13 | Mi perfil | `/perfil/` | `views.cuentas.perfil` |
| HU14 | Registrar kilometraje | `/kilometraje/` | `views.kilometraje.registrar` |
| HU15 | Detalle del vehículo | `/vehiculos/<id>/` | `views.vehiculos.detalle` |

## Reglas de negocio

- **Estado documental:** `Vigente`, `Próximo a vencer` (dentro del umbral
  mayor configurado), `Vencido` y `Sin registro` cuando aún no hay fechas.
- **Estado de mantenimiento:** `Pendiente` pasa a `Atrasado` al superarse la
  fecha o alcanzarse el kilometraje objetivo, y a `Cumplido` de forma
  irreversible, guardando fecha y kilometraje del momento.
- **Criterio excluyente:** un mantenimiento se programa por fecha o por
  kilometraje, nunca por ambos.
- **Baja lógica:** el vehículo sale del listado y del panel pero conserva
  documentos e historial; ninguna vista de escritura lo admite, ni por URL.
- **Kilometraje:** histórico de lecturas, nunca menor al último registrado ni
  con fecha futura; al guardarlo se reevalúan los mantenimientos por kilometraje.
- **Aislamiento de flota:** validado en el backend; un vehículo ajeno responde
  404 y resulta indistinguible de uno inexistente.
- **Perfil:** cambiar correo o contraseña cierra la sesión activa.

## Alertas automáticas (HU11)

El envío no es en tiempo real; se ejecuta con un management command:

```bash
python manage.py enviar_alertas --dry-run
python manage.py enviar_alertas
```

Programación diaria sugerida:

```
0 7 * * * cd /ruta/alvolante && python manage.py enviar_alertas
```

Las alertas se emiten durante toda la ventana configurada, no solo el día
exacto del umbral: si el cron no corre un día, la notificación no se pierde. En
desarrollo el correo se imprime en consola.

## Siguiente paso

Reemplazar los repositorios en memoria por modelos del ORM sobre PostgreSQL 16
y migrar la autenticación a `django.contrib.auth`.
