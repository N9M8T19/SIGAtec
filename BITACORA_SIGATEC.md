# SIGA-Tec — Bitácora del Proyecto
**E.T. N°7 D.E. 5 — Dolores Lavalle de Lavalle**
**Última actualización: 01/05/2026 (sesión 38)**

---

## 📋 Descripción del sistema

Sistema Integral de Gestión de Recursos Tecnológicos (SIGA-Tec).
Gestiona carros de netbooks, préstamos a docentes, Espacio Digital, pantallas digitales, televisores, control de stock, asignación de alumnos por turno, tickets BA Colaborativa, mensajería interna entre el equipo, obsolescencia y reemplazos de netbooks e importación desde Google Drive.

- **Framework:** Flask (Python 3.11)
- **Base de datos:** SQLite (local) / PostgreSQL (producción)
- **Login:** Google OAuth2 (solo cuentas autorizadas)
- **Deploy:** Render (producción activa)
- **URL producción:** https://sigatec-et7.onrender.com
- **Repo GitHub:** https://github.com/N9M8T19/SIGAtec.git

---

## 🏗️ Estructura del proyecto

```
SIGAtec_web/
├── app.py                          # ⚠️ Actualizado 15/04/2026 — fix zona horaria (ARG_OFFSET = -3)
│                                   # ⚠️ Actualizado 16/04/2026 — registra sesiones_bp
│                                   # ⚠️ Actualizado 24/04/2026 — registra asignaciones_bp, tvs_bp
│                                   # ⚠️ Actualizado 27/04/2026 — elimina ubicaciones_bp (módulo descartado)
│                                   # ⚠️ Actualizado 29/04/2026 (sesión 22) — registra mensajeria_bp
│                                   # ⚠️ Actualizado 30/04/2026 (sesión 27) — registra obsolescencia_bp
│                                   # ⚠️ Actualizado 30/04/2026 (sesión 29) — context_processor inject_secciones_encargado
├── config.py                       # Configuración Flask + Mail + DB — MINUTOS_ALERTA_PRESTAMO = 260 (4h 20min)
├── models/
│   ├── __init__.py                 # ⚠️ Actualizado 30/04/2026 (sesión 29) — Usuario: campo secciones_json + métodos get_secciones/set_secciones
│   │                               # ⚠️ Actualizado 29/04/2026 (sesión 26) — TicketBA: campos estado/fecha_cierre/motivo_cierre/cerrado_por
│   │                               # ⚠️ Actualizado 29/04/2026 (sesión 22) — modelos Mensaje y MensajeLeid (mensajería interna)
│   │                               # ⚠️ Actualizado 28/04/2026 (sesión 18) — PrestamoCarro: campo materia_prestamo
│   │                               # ⚠️ Actualizado 27/04/2026 — TV: ABM + componentes + préstamos
│   │                               # ⚠️ Actualizado 27/04/2026 — PrestamoTV: préstamos de televisores
│   │                               # ⚠️ Actualizado 24/04/2026 — AsignacionInterna: modelo sin FK a netbooks (campo libre)
│   │                               # ⚠️ Actualizado 22/04/2026 — TicketBANetbook: campo carro_id + relationship a Carro
│   │                               # ⚠️ Actualizado 20/04/2026 — ConfigEspacioDigital: campo carro_id_2 y relación carro_2
│   │                               # ⚠️ Actualizado 15/04/2026 — modelo Carro: estado/motivo_servicio/fecha_servicio
│   ├── config_sistema.py           # ⚠️ Actualizado 01/05/2026 (sesión 38) — campos mail_retiro_tv y mail_devolucion_tv
│   │                               # ⚠️ Actualizado 30/04/2026 (sesión 29) — SECCIONES_DISPONIBLES: lista completa de 26 secciones habilitables
│   │                               # ⚠️ Actualizado 30/04/2026 (sesión 29) — ConfigSistema: campo secciones_encargado_json + get/set_secciones_encargado
│   └── sesion.py                   # ⚠️ Nuevo 16/04/2026 — modelo SesionEncargado
├── models_extra/
│   ├── __init__.py
│   └── horarios_notificaciones.py  # HorarioDocente, ConfigNotificacion, LogNotificacion
│                                   # + lista MATERIAS (68 materias) + MODULOS corregidos
├── routes/
│   ├── auth.py                     # ⚠️ Actualizado 16/04/2026 — registra sesión al login, cierra al logout
│   ├── alumnos.py                  # ⚠️ Actualizado 08/04/2026 — paginación server-side (50/pág)
│   ├── asignaciones.py             # ⚠️ Nuevo 24/04/2026 — ABM Asignaciones Internas (solo Directivo/Admin)
│   ├── carros.py                   # ⚠️ Actualizado 28/04/2026 — netbooks() y asignar_automatico() ordenan por numero_interno numérico
│   │                               # ⚠️ Actualizado 15/04/2026 — endpoints enviar_servicio y recuperar_carro
│   ├── docentes.py                 # ⚠️ Actualizado 29/04/2026 (sesión 24) — usa _get_materias_activas() en nuevo() y editar()
│   │                               # ⚠️ Actualizado 15/04/2026 — fix IntegrityError: elimina préstamos históricos antes del delete
│   │                               # ⚠️ Actualizado 14/04/2026 — fix error 500 al confirmar jubilación
│   │                               # ⚠️ Actualizado 08/04/2026 — baja con motivo, jubilación elimina
│   ├── etiquetas.py                # ⚠️ Actualizado 27/04/2026 — agrega endpoints para TVs, Pantallas e Impresoras 3D
│   ├── horarios.py                 # ⚠️ Actualizado 21/04/2026 — nuevo endpoint GET /horarios/docente/<id>/pdf
│   ├── importar.py                 # ⚠️ Actualizado 21/04/2026 — rutas horarios_docentes y horarios_docentes_preview (Excel + Sheets)
│   ├── main.py                     # ⚠️ Actualizado 01/05/2026 (sesión 38) — config_sistema() guarda/pasa mail_retiro_tv y mail_devolucion_tv
│   │                               # ⚠️ Actualizado 01/05/2026 (sesión 38) — agrega _mail_default_retiro_tv() y _mail_default_devolucion_tv()
│   │                               # ⚠️ Actualizado 30/04/2026 (sesión 29) — config_sistema() agrega acción guardar_secciones + pasa secciones al template
│   │                               # ⚠️ Actualizado 28/04/2026 (sesión 18) — /estadisticas agrega top_docentes y top_materias por materia_prestamo
│   │                               # ⚠️ Actualizado 28/04/2026 (sesión 17) — nueva ruta GET /estadisticas (solo Directivo/Admin)
│   │                               # ⚠️ Actualizado 27/04/2026 — dashboard suma tvs_prestadas a stats
│   │                               # ⚠️ Actualizado 27/04/2026 — /api/novedades incluye préstamos y devoluciones de TVs
│   │                               # ⚠️ Actualizado 22/04/2026 — /api/novedades incluye carros y netbooks enviados a servicio técnico hoy
│   │                               # ⚠️ Actualizado 20/04/2026 — config_espacio_digital guarda carro_id_2, valida que no sean iguales
│   │                               # ⚠️ Actualizado 14/04/2026 — config_espacio_digital habilitado para Encargado
│   ├── mantenimiento.py            # ⚠️ Actualizado 01/05/2026 (sesión 38) — importa PrestamoTV; borrado en modo docente, activos e individual
│   │                               # ⚠️ Actualizado 01/05/2026 (sesión 38) — prestamos_docente() incluye TVs en JSON; borrar_prestamos_individuales() soporta ids_tvs
│   ├── netbooks.py                 # ⚠️ Actualizado 28/04/2026 — validación número interno duplicado por carro en nuevo() y editar()
│   │                               # ⚠️ Actualizado 28/04/2026 — nuevo endpoint GET /netbooks/verificar-numero-interno (AJAX)
│   │                               # ⚠️ Actualizado 28/04/2026 — servicio_tecnico() ordena por numero_interno numérico
│   │                               # ⚠️ Actualizado 20/04/2026 — validación número de serie duplicado en nuevo() y editar()
│   │                               # ⚠️ Actualizado 20/04/2026 — nuevo endpoint GET /netbooks/verificar-serie (AJAX)
│   │                               # ⚠️ Actualizado 15/04/2026 — servicio_tecnico() pasa carros_servicio al template
│   ├── notificaciones.py
│   ├── obsolescencia.py            # ⚠️ Nuevo 30/04/2026 (sesión 27) — ABM obsolescencia + reemplazos + pendientes
│   │                               # ⚠️ Actualizado 30/04/2026 (sesión 28) — fix: quita n.modelo (columna inexistente en BD)
│   ├── pantallas.py
│   ├── prestamos.py                # ⚠️ Actualizado 01/05/2026 (sesión 32) — retiro_netbooks() pasa 4 listas separadas por carro
│   │                               # ⚠️ Actualizado 01/05/2026 (sesión 32) — espacio_digital() pasa nb_carro_map + carro_id_1/2
│   │                               # ⚠️ Actualizado 28/04/2026 (sesión 18) — retiro_carro() guarda materia_prestamo del módulo actual
│   │                               # ⚠️ Actualizado 27/04/2026 — carros() pasa tvs_prestadas al template
│   │                               # ⚠️ Actualizado 20/04/2026 — espacio_digital() y retiro_netbooks() soportan carro_id_2
│   │                               # ⚠️ Actualizado 16/04/2026 — endpoints alerta_pdf_carro y alerta_pdf_netbooks
│   │                               # ⚠️ Actualizado 15/04/2026 — retiro_carro bloquea carros en_servicio
│   │                               # ⚠️ Actualizado 15/04/2026 — nuevo endpoint devolucion_netbook_individual
│   │                               # ⚠️ Actualizado 08/04/2026 — prestamos_activos_ids en retiro_carro
│   ├── reportes.py
│   ├── sesiones.py                 # ⚠️ Nuevo 16/04/2026 — listado, cierre individual y cierre masivo de sesiones
│   ├── stock.py                    # ⚠️ Actualizado 24/04/2026 — _procesar_control_masivo() incluye asignaciones internas
│   │                               # ⚠️ Actualizado 22/04/2026 (sesión 12) — fix PDF: session guarda solo series
│   │                               # ⚠️ Actualizado 22/04/2026 (sesión 11) — control masivo: rutas control_masivo y control_masivo_pdf
│   ├── tickets_ba.py               # ⚠️ Actualizado 29/04/2026 (sesión 26) — cerrar()/reabrir() reemplazan eliminar() para activos
│   │                               # ⚠️ Actualizado 22/04/2026 — index() pasa carros_en_servicio + nuevo() guarda carro_ids
│   ├── transferencias.py           # ⚠️ Actualizado 15/04/2026 — index() acepta carro_origen_id precargado
│   ├── tvs.py                      # ⚠️ Actualizado 01/05/2026 (sesión 35) — prestar() y devolver() llaman enviar_notificacion_retiro/devolucion_tv
│   │                               # ⚠️ Actualizado 29/04/2026 (sesión 25) — prestar: buscador autocomplete de docente
│   │                               # ⚠️ Nuevo 27/04/2026 — ABM TVs + préstamos + historial + etiquetas
│   ├── usuarios.py                 # ⚠️ Actualizado 30/04/2026 (sesión 29) — editar()/nuevo() guardan secciones_json + pasan SECCIONES_DISPONIBLES al template
│   └── mensajeria.py               # ⚠️ Nuevo 29/04/2026 (sesión 22) — chat interno: 4 canales, avisos rápidos, polling, badges
├── services/
│   ├── alertas_horario.py
│   ├── backup.py
│   ├── importar_drive.py           # ⚠️ Actualizado 28/04/2026 (sesión 19) — fix normalización horarios Excel + acumulación módulos
│   │                               # ⚠️ Actualizado 21/04/2026 — importar_horarios_docentes() vía Google Sheets
│   ├── mail.py                     # ⚠️ Actualizado 01/05/2026 (sesión 38) — enviar_notificacion_retiro/devolucion_tv usan _get_template_mail()
│   │                               # ⚠️ Actualizado 01/05/2026 (sesión 36) — fix SyntaxError backslash en f-string (pulgadas_str)
│   │                               # ⚠️ Actualizado 01/05/2026 (sesión 35) — agrega enviar_notificacion_retiro_tv() y enviar_notificacion_devolucion_tv()
│   │                               # ⚠️ Actualizado 06/04/2026 — mails directos al docente
│   └── pdf_reportes.py             # ⚠️ Actualizado 01/05/2026 (sesión 32) — pdf_alerta_demora_netbooks() agrupa ítems por carro con sub-encabezado azul
│                                   # ⚠️ Actualizado 01/05/2026 (sesión 32) — agrega constante AZUL_OSCURO = #1a2a6c
│                                   # ⚠️ Actualizado 28/04/2026 (sesión 18) — pdf_estadisticas() muestra materia discriminada por módulo
│                                   # ⚠️ Actualizado 27/04/2026 — pdf_historial_tvs() + pdf_etiquetas_tvs()
│                                   # ⚠️ Actualizado 22/04/2026 — pdf_control_masivo_stock(): landscape, resumen + 3 secciones
│                                   # ⚠️ Actualizado 21/04/2026 — pdf_horario_docente(): PDF landscape por docente con carro asignado
│                                   # ⚠️ Actualizado 20/04/2026 — historial landscape + columnas Autorizó Retiro/Devolución + Carro(s)
│                                   # ⚠️ Actualizado 16/04/2026 — pdf_alerta_demora_carro y pdf_alerta_demora_netbooks
│                                   # ⚠️ Actualizado 15/04/2026 — pdf_servicio_tecnico incluye carros físicos
├── templates/
│   ├── base.html                   # ⚠️ Actualizado 30/04/2026 (sesión 31) — secciones Admin/Directivo también habilitables para Encargado
│   │                               # ⚠️ Actualizado 30/04/2026 (sesión 29) — links del sidebar controlados por secciones_enc
│   │                               # ⚠️ Actualizado 30/04/2026 (sesión 27) — link Obsolescencia en sidebar
│   │                               # ⚠️ Actualizado 29/04/2026 (sesión 22) — link Mensajería + badge no leídos
│   │                               # ⚠️ Actualizado 28/04/2026 (sesión 17) — link Estadísticas (solo Directivo/Admin)
│   │                               # ⚠️ Actualizado 27/04/2026 — link Televisores; elimina link Ubicaciones
│   │                               # ⚠️ Actualizado 24/04/2026 — link Asignaciones Internas (solo Directivo/Admin)
│   │                               # ⚠️ Actualizado 22/04/2026 — link Stock Masivo
│   │                               # ⚠️ Actualizado 21/04/2026 — link Horarios Docentes
│   │                               # ⚠️ Actualizado 16/04/2026 — link Sesiones (Admin/Directivo)
│   ├── mantenimiento/
│   │   └── limpiar_pruebas.html    # ⚠️ Actualizado 01/05/2026 (sesión 38) — tarjeta TVs activas en sección 2; tabla de TVs en sección 3; JS actualizado
│   ├── obsolescencia/              # ⚠️ Nuevo 30/04/2026 (sesión 27)
│   │   ├── index.html
│   │   ├── nueva.html
│   │   └── reemplazo.html
│   ├── mensajeria/                 # ⚠️ Nuevo 29/04/2026 (sesión 22)
│   │   └── index.html
│   ├── main/
│   │   ├── estadisticas.html       # ⚠️ Nuevo 28/04/2026 (sesión 17)
│   │   └── config_sistema.html     # ⚠️ Actualizado 01/05/2026 (sesión 38) — 2 textareas para TV; placeholders {tv}, {aula_destino}, {motivo}, {componentes}
│   ├── usuarios/
│   │   └── form.html               # ⚠️ Actualizado 30/04/2026 (sesión 29) — grilla de secciones habilitables para Encargado
│   ├── asignaciones/               # ⚠️ Nuevo 24/04/2026
│   │   ├── index.html
│   │   └── form.html
│   ├── docentes/
│   ├── alumnos/
│   ├── carros/
│   ├── etiquetas/
│   ├── impresoras3d/
│   ├── netbooks/
│   ├── sesiones/
│   ├── horarios/
│   ├── importar/
│   ├── stock/
│   ├── tvs/
│   │   ├── index.html
│   │   ├── form.html
│   │   ├── prestar.html            # ⚠️ Actualizado 29/04/2026 (sesión 25)
│   │   ├── devolver.html
│   │   ├── prestamos.html
│   │   └── historial.html
│   └── prestamos/
│       ├── carros.html
│       ├── retiro_carro.html
│       ├── espacio_digital.html    # ⚠️ Actualizado 01/05/2026 (sesión 32) — agrupa netbooks por carro con sub-encabezados
│       ├── historial.html
│       └── retiro_netbooks.html    # ⚠️ Actualizado 01/05/2026 (sesión 34) — fix block content duplicado
│                                   # ⚠️ Actualizado 01/05/2026 (sesión 33) — layout grid-cols-2 side by side, max-w-5xl
│                                   # ⚠️ Actualizado 01/05/2026 (sesión 32) — disponibles/prestadas separadas y grisadas por carro
├── templates/tickets_ba/
│   └── index.html                  # ⚠️ Actualizado 29/04/2026 (sesión 26)
├── static/img/
│   ├── logo_escuela.png
│   └── logo_SIGA-tec.png
├── migrate_mail_tv.py              # ⚠️ Nuevo 01/05/2026 (sesión 38) — agrega mail_retiro_tv y mail_devolucion_tv a config_sistema
├── migrate_secciones_encargado.py  # ⚠️ Nuevo 30/04/2026 (sesión 29)
├── migrate_secciones_usuario.py    # ⚠️ Nuevo 30/04/2026 (sesión 29)
├── migrate_obsolescencia.py        # ⚠️ Nuevo 30/04/2026 (sesión 27)
├── migrate_ticket_ba_estado.py     # ⚠️ Nuevo 29/04/2026 (sesión 26)
├── migrate_materia_prestamo.py     # ⚠️ Nuevo 28/04/2026 (sesión 18)
├── migrate_mensajeria.py           # ⚠️ Nuevo 29/04/2026 (sesión 22)
├── migrate_tvs.py                  # ⚠️ Nuevo 27/04/2026
├── migrate_asignaciones_internas.py
├── migrate_ticket_ba_carro.py
├── migrate_config_espacio_digital_2.py
├── migrate_estado_carro.py
├── migrate_sesiones.py
├── migrate_impresoras3d.py
├── migrate_alumnos.py
├── migrate_baja_netbook.py
├── migrate_reclamo.py
├── migrate_netbook_alumno.py
├── requirements.txt                # ⚠️ Actualizado 21/04/2026 — agrega openpyxl==3.1.2
├── credentials.json                # (NO subir a GitHub)
├── service_account.json            # (NO subir a GitHub)
├── token.json                      # (NO subir a GitHub)
├── .env                            # (NO subir a GitHub)
├── .gitignore
├── .python-version
├── Procfile
└── render.yaml
```

---

## 🚀 Deploy en Render — configuración actual

### Servicio
- **Nombre:** sigatec-et7
- **URL:** https://sigatec-et7.onrender.com
- **Plan:** Starter
- **Runtime:** Python 3.11 (forzado via `.python-version`)
- **Start Command:** `gunicorn "app:create_app()"`
- **Build Command:** `pip install "psycopg2-binary==2.9.6" && pip install -r requirements.txt`

### Base de datos
- **Nombre:** sigartec-db
- **Motor:** PostgreSQL
- **Plan:** Free

### Variables de entorno en Render
| Variable | Valor |
|----------|-------|
| `SECRET_KEY` | Generada por Render |
| `DATABASE_URL` | Conexión interna PostgreSQL (automática) |
| `GOOGLE_CLIENT_ID` | `413295040550-gg1kbqa7lmsj79kr845fkk1fe1urv878.apps.googleusercontent.com` |
| `GOOGLE_CLIENT_SECRET` | Configurado manualmente en Render |
| `FLASK_ENV` | `production` |
| `GMAIL_USER` | `aulamagnaespaciodigital@gmail.com` |
| `GMAIL_APP_PASSWORD` | App Password de 16 caracteres |

---

## 🗄️ Modelos de base de datos

| Modelo | Tabla | Descripción |
|--------|-------|-------------|
| `Usuario` | `usuarios` | Encargados, directivos, admin — campo `secciones_json` para secciones habilitadas por usuario |
| `Docente` | `docentes` | Docentes con turno, materia, correo |
| `Carro` | `carros` | Carros de netbooks — campos `estado`, `motivo_servicio`, `fecha_servicio` |
| `Alumno` | `alumnos` | Alumnos con curso, turno (M/T) y FK a netbook asignada |
| `Netbook` | `netbooks` | Netbooks con FK a carro, alumnos |
| `PrestamoCarro` | `prestamos_carros` | Préstamos de llaves/carros — campo `materia_prestamo` |
| `PrestamoNetbook` | `prestamos_netbooks` | Préstamos del Espacio Digital |
| `PrestamoNetbookItem` | `prestamo_netbook_items` | Items de cada préstamo netbook |
| `ConfigEspacioDigital` | `config_espacio_digital` | Carros asignados al Espacio Digital — soporta hasta 2 carros |
| `PantallaDigital` | `pantallas_digitales` | Pizarrones interactivos |
| `HistorialPantalla` | `historial_pantallas` | Historial de eventos de pantallas |
| `TicketBA` | `tickets_ba` | Tickets BA Colaborativa — campos `estado`, `fecha_cierre`, `motivo_cierre`, `cerrado_por` |
| `TicketBANetbook` | `tickets_ba_netbooks` | Equipos vinculados a tickets |
| `HorarioDocente` | — | Módulos por día para cada docente |
| `ConfigNotificacion` | — | Destinatarios de alertas |
| `LogNotificacion` | — | Log de notificaciones enviadas |
| `Impresora3D` | `impresoras_3d` | Impresoras 3D |
| `SesionEncargado` | `sesiones_encargados` | Registro de inicios de sesión de encargados |
| `AsignacionInterna` | `asignaciones_internas` | Netbooks asignadas a docentes o áreas fuera de carros |
| `TV` | `tvs` | Televisores — código, marca, modelo, pulgadas, aula, estado, componentes |
| `PrestamoTV` | `prestamos_tvs` | Préstamos de televisores |
| `ConfigSistema` | `config_sistema` | Configuración editable: materias, módulos, templates de mail (carros, netbooks y TVs), secciones globales del Encargado |
| `Mensaje` | `mensajes` | Mensajes de mensajería interna — canal, autor, tipo |
| `MensajeLeid` | `mensajes_leidos` | Registro de lecturas — para badges de no leídos |
| — | `obsolescencias` | Netbooks obsoletas y sus reemplazos — tabla sin modelo ORM, accedida con psycopg2 directo |

### Roles y permisos

| Rol | Permisos |
|-----|----------|
| `Encargado` | Secciones configurables individualmente por usuario (o globalmente desde Config. Sistema) |
| `Directivo` | Todo igual que Administrador |
| `Administrador` | Todo, incluyendo editar username/correo de otros usuarios |

---

## ⏰ Zona horaria

- La BD guarda en **UTC**
- La app muestra en **Argentina (UTC-3)**
- `ARG_OFFSET = timedelta(hours=-3)` — definido en `app.py` y `pdf_reportes.py`
- Filtros Jinja2: `{{ fecha|arg_datetime }}`, `{{ fecha|arg_time }}`, `{{ fecha|arg_date }}`

---

## 📧 Sistema de mails

- **Método:** SMTP con Gmail App Password
- **Cuenta remitente:** `aulamagnaespaciodigital@gmail.com`
- **Librería:** `smtplib` (estándar de Python)
- **Templates editables desde Config. Sistema:** retiro/devolución de carros, netbooks y TVs

---

## 📄 Documentación externa generada

| Documento | Descripción | Fecha |
|-----------|-------------|-------|
| `Manual_SIGA-Tec.pdf` | Manual de usuario completo (13 secciones). | 06/04/2026 |
| `LISTADOS_SIGATEC_2026.xlsx` | Listados de alumnos 2026. 28 pestañas NxGy TM/TT. | 08/04/2026 |

---

## ✅ Funcionalidades completadas

- [x] Login con Google OAuth2
- [x] ABM de carros, netbooks, docentes, usuarios
- [x] Préstamos de carros con control de turno del docente
- [x] Espacio Digital (préstamo de netbooks individuales)
- [x] Historial con filtros por período y fechas personalizadas
- [x] Horarios de docentes — 15 módulos con horarios reales
- [x] Notificaciones por mail
- [x] Alertas automáticas por fin de módulo y por demora
- [x] Backup automático SQLite + descarga manual
- [x] Pantallas digitales con historial
- [x] Control de stock por carro
- [x] Transferencia de netbooks entre carros + PDF
- [x] Importación desde Google Sheets
- [x] PDFs de todos los reportes con logo de escuela
- [x] Zona horaria Argentina en toda la app
- [x] Mi Perfil (editar nombre, apellido, username)
- [x] Asignación de alumnos a netbooks por turno
- [x] Importación de alumnos desde Google Sheets
- [x] Dar de baja netbooks con motivo + PDF
- [x] Servicio técnico de netbooks con motivo obligatorio
- [x] Tickets BA Colaborativa
- [x] Selector de materia con buscador desplegable (68 materias)
- [x] Colores del escudo de la escuela en toda la app
- [x] Pantalla de login con logo SIGA-Tec
- [x] Admin/Directivo pueden editar username y correo de otros usuarios
- [x] **Deploy en Render con PostgreSQL** ✅ (02/04/2026)
- [x] **Manual de usuario en PDF** ✅ (06/04/2026)
- [x] **Notificaciones automáticas por mail** ✅ (06/04/2026)
- [x] **Mail directo al docente** ✅ (06/04/2026)
- [x] **Listados de alumnos 2026** ✅ (08/04/2026)
- [x] **Módulo Alumnos** ✅ (08/04/2026)
- [x] **Asignación automática de netbooks a alumnos** ✅ (08/04/2026)
- [x] **Importación de alumnos desde Google Sheets** ✅ (08/04/2026)
- [x] **Búsqueda global en el dashboard** ✅ (08/04/2026)
- [x] **Baja de docente con selector de motivo** ✅ (08/04/2026)
- [x] **Paginación en el módulo Alumnos** ✅ (08/04/2026)
- [x] **Búsqueda en tiempo real en listado de Docentes** ✅ (08/04/2026)
- [x] **Estado visual de carros en préstamos** ✅ (08/04/2026)
- [x] **Dashboard rediseñado** ✅ (09/04/2026)
- [x] **Módulo Impresoras 3D** ✅ (14/04/2026)
- [x] **Config. Espacio Digital habilitada para Encargado** ✅ (14/04/2026)
- [x] **Fix error 500 al dar de baja docente por jubilación** ✅ (14/04/2026)
- [x] **Fix IntegrityError al dar de baja docente por jubilación** ✅ (15/04/2026)
- [x] **Fix zona horaria** ✅ (15/04/2026)
- [x] **Devolución individual de netbooks en Espacio Digital** ✅ (15/04/2026)
- [x] **Servicio técnico de carro físico** ✅ (15/04/2026)
- [x] **Pantalla Servicio Técnico unificada** ✅ (15/04/2026)
- [x] **Transferencias precargadas desde servicio técnico** ✅ (15/04/2026)
- [x] **PDF Parte de Alerta — Préstamos en Demora** ✅ (16/04/2026)
- [x] **Módulo Sesiones de Encargados** ✅ (16/04/2026)
- [x] **Espacio Digital con 2 carros** ✅ (20/04/2026)
- [x] **Validación número de serie duplicado en netbooks** ✅ (20/04/2026)
- [x] **Historial: Autorizó Retiro, Autorizó Devolución y Carro — PDF landscape** ✅ (20/04/2026)
- [x] **Importación masiva de horarios de docentes** ✅ (21/04/2026)
- [x] **PDF de horario de docente con carro asignado** ✅ (21/04/2026)
- [x] **Tickets BA: carros en servicio seleccionables sin netbooks** ✅ (22/04/2026)
- [x] **Dashboard: servicio técnico en Novedades del día** ✅ (22/04/2026)
- [x] **Control Masivo de Stock** ✅ (22/04/2026)
- [x] **Fix PDF control masivo — desborde de session** ✅ (22/04/2026)
- [x] **Módulo Asignaciones Internas** ✅ (24/04/2026)
- [x] **Módulo Televisores completo** ✅ (27/04/2026)
- [x] **Orden numérico de netbooks + validación número interno duplicado** ✅ (28/04/2026 — sesión 16)
- [x] **Módulo Estadísticas de Préstamos** ✅ (28/04/2026 — sesión 17)
- [x] **Materia discriminada por módulo en estadísticas** ✅ (28/04/2026 — sesión 18)
- [x] **Fix importación de horarios Excel** ✅ (28/04/2026 — sesión 19)
- [x] **Módulo Configuración del Sistema** ✅ (29/04/2026 — sesión 20)
- [x] **Cantidad de netbooks en mails de carro + detalle items en mails de Espacio Digital** ✅ (29/04/2026 — sesión 21)
- [x] **Mensajería Interna** ✅ (29/04/2026 — sesión 22)
- [x] **Filtro por rango horario en historial de préstamos** ✅ (29/04/2026 — sesión 23)
- [x] **Fix selector de materias en formulario de docentes** ✅ (29/04/2026 — sesión 24)
- [x] **Buscador de docente en préstamo de TV** ✅ (29/04/2026 — sesión 25)
- [x] **Tickets BA: cierre/archivo de tickets resueltos** ✅ (29/04/2026 — sesión 26)
- [x] **Módulo Obsolescencia y Reemplazos de Netbooks** ✅ (30/04/2026 — sesión 27)
- [x] **Fix obsolescencia — columna n.modelo inexistente** ✅ (30/04/2026 — sesión 28)
- [x] **Secciones habilitables para Encargado — Config. Sistema (global)** ✅ (30/04/2026 — sesión 29)
- [x] **Secciones habilitables por Encargado — configuración por usuario** ✅ (30/04/2026 — sesión 30)
- [x] **Secciones Admin/Directivo habilitables para Encargado** ✅ (30/04/2026 — sesión 31)
- [x] **Espacio Digital: listas separadas por carro, grisado de prestadas, detalle agrupado por carro, parte de alerta por carro** ✅ (01/05/2026 — sesión 32)
- [x] **Layout dos columnas side by side en retiro de netbooks** ✅ (01/05/2026 — sesión 33)
- [x] **Fix block content duplicado en retiro_netbooks.html** ✅ (01/05/2026 — sesión 34)
- [x] **Mail de retiro y devolución de TVs al docente** ✅ (01/05/2026 — sesión 35)
  - `routes/tvs.py`: `prestar()` y `devolver()` llaman a las nuevas funciones de mail en `try/except`
  - `services/mail.py`: `enviar_notificacion_retiro_tv()` y `enviar_notificacion_devolucion_tv()` con componentes y faltantes
- [x] **Fix SyntaxError backslash en f-string de mails de TV** ✅ (01/05/2026 — sesión 36)
  - **Causa:** Python 3.11 no permite `\"` dentro de expresiones en f-strings
  - **Solución:** `pulgadas_str = f' ({tv.pulgadas}")'` extraído como variable previa al f-string
- [x] **Templates de mail de TV editables desde Config. Sistema** ✅ (01/05/2026 — sesión 38)
  - `models/config_sistema.py`: columnas `mail_retiro_tv` y `mail_devolucion_tv`
  - `routes/main.py`: guarda/pasa los nuevos templates; `_mail_default_retiro_tv()` y `_mail_default_devolucion_tv()`
  - `services/mail.py`: funciones de TV usan `_get_template_mail()` si hay template configurado
  - `templates/main/config_sistema.html`: 2 textareas nuevos; placeholders `{tv}`, `{aula_destino}`, `{motivo}`, `{componentes}` documentados
  - `migrate_mail_tv.py`: agrega las columnas a `config_sistema` en producción
- [x] **Historial de TVs en Administrar Historial** ✅ (01/05/2026 — sesión 38)
  - `routes/mantenimiento.py`: borra TVs en los tres modos (docente, activos, individual); JSON incluye préstamos de TV
  - `templates/mantenimiento/limpiar_pruebas.html`: tarjeta "TVs activas" en sección 2; tabla de Televisores en sección 3 con checkboxes y JS extendido

---

## 🔜 Pendiente

- [ ] Escanear código de barras al agregar netbook
- [ ] Botón Parte de Alerta en pantalla Espacio Digital (análogo al de carros)
- [ ] Integrar pendientes de obsolescencia en /api/novedades del dashboard
- [ ] Actualizar el Manual de usuario PDF con los módulos nuevos

---

## 👤 Usuario administrador

- **DNI:** 41469656
- **Username:** admin
- **Nombre:** N. Montefinal Turnes
- **Correo Google:** nicolas.montefinal@bue.edu.ar
- **Rol:** Administrador

---

## 🛠️ Problemas resueltos durante el desarrollo

### psycopg2 incompatible con Python 3.14
Render usaba Python 3.14 por defecto. Solución: archivo `.python-version` con `3.11.0`.

### Archivos secretos bloqueados por GitHub
GitHub Push Protection bloqueó el push. Solución: `git rm --cached` y `.gitignore`.

### Notificaciones por mail — migración de Gmail API a SMTP
`mail.py` usaba Gmail API con `token.json` que no puede subirse a Render. Solución: reescribir con `smtplib` y Gmail App Password.

### OAUTHLIB_INSECURE_TRANSPORT en producción
Condicionado solo cuando `FLASK_ENV != production`.

### Listados de alumnos con estructura heterogénea
Procesamiento con pandas + openpyxl detectando estructura por fila.

### Cursos importados con nombre de pestaña completo
Corregir 794 registros con UPDATE directo + actualizar `importar_drive.py`.

### Ruta `asignar_automatico` duplicada en carros.py
Flask lanzó `AssertionError`. Solución: reemplazar con versión limpia.

### Búsqueda global — error 500 por campos y rutas incorrectos
Reescribir endpoint con campos y rutas correctos.

### Baja de docente — campo `devuelto` inexistente en PrestamoCarro
Corregir query a `filter_by(docente_id=id, estado='activo')`.

### Carros prestados no se mostraban en rojo en retiro_carro.html
Renombrar variable a `prestamos_activos_ids`.

### Config. Espacio Digital inaccesible para Encargado
Extender condición de acceso en `main.py` y separar link en `base.html`.

### Error 500 al confirmar baja por jubilación — DetachedInstanceError
Guardar nombre en variable local antes del delete.

### IntegrityError al dar de baja docente por jubilación
PostgreSQL rechaza `docente_id = NULL`. Solución: eliminar préstamos antes del delete.

### Zona horaria incorrecta
`ARG_OFFSET = timedelta(hours=3)` sumaba en lugar de restar. Fix: `timedelta(hours=-3)`.

### Modal servicio técnico no abría
El modal y el `<script>` quedaron dentro de `{% block title %}`. Fix: reestructurar bloques.

### Módulo Sesiones — import `extensions` inexistente
Reemplazar `from extensions import db` por `from models import db`.

### Módulo Sesiones — filtro `pluralize` inexistente en Jinja2
Reemplazar por `{% if total_activas != 1 %}s{% endif %}`.

### Espacio Digital — migración `carro_id_2` con error `commit` en SQLAlchemy 1.x
Usar `db.engine.execute()` directo en lugar de `conn.commit()`.

### Rutas duplicadas en importar.py — AssertionError al deployar
Eliminar las rutas duplicadas dejando solo la versión con soporte Excel + Sheets.

### openpyxl no instalado en producción
Agregar `openpyxl==3.1.2` a `requirements.txt`.

### Nombre de docente invertido al importar Excel
Usar siempre `_nombre_desde_archivo()` ignorando el contenido de la planilla.

### Tickets BA — carros físicos en servicio no aparecían para seleccionar
Agregar campo `carro_id` al modelo con migración, actualizar rutas y template.

### PDF control masivo — session de Flask desbordada (~4 KB límite)
Guardar solo la lista de series y reprocesar queries al generar el PDF.

### Asignaciones Internas — migración falla con SQLAlchemy 1.x
Reescribir usando `psycopg2` directamente con `conn.autocommit = True`.

### Asignaciones Internas — error 500 en dashboard (columna `fecha_servicio` inexistente)
`ALTER TABLE netbooks ADD COLUMN IF NOT EXISTS fecha_servicio TIMESTAMP;` desde la Shell de Render.

### Deploy fallido por ImportError de ubicaciones_bp
Eliminar el import y registro de `ubicaciones_bp` en `app.py`.

### PDF historial de TVs desbordado en A4 landscape
Las 9 columnas sumaban más de 400mm. Reducir anchos para quedar dentro de ~247mm.

### Netbooks desordenadas — ordenamiento lexicográfico incorrecto
`numero_interno` es String; `sort(key=lambda nb: int(nb.numero_interno) if nb.numero_interno and nb.numero_interno.isdigit() else 9999)`.

### Error 500 en /estadisticas — CAST AS INTEGER falla con numero_fisico no numérico
Ordenar en Python con `int()` en lugar de SQL CAST.

### Módulos de horario no se importan desde Excel
Planilla usa `8.10 a 8.50`. `_normalizar_horario()` reescrita con `zfill` y normalización de separadores.

### Docente con turno Varios pierde módulos al importar la segunda planilla
Lógica de acumulación que verifica si el slot ya existe antes de insertar.

### Mensajería interna — Error 500 (Table 'mensajes' is already defined)
`_get_models()` en `routes/mensajeria.py` creaba clases dinámicas que colisionaban con el MetaData. Solución: `from models import db, Mensaje, MensajeLeid`.

### Filtro horario en historial no convierte correctamente a UTC
Aplicar `ARG_OFFSET` al `datetime` completo antes de comparar.

### Cargos de Config. Sistema no aparecen en selector de materia
`routes/docentes.py` importaba `MATERIAS` hardcodeada al arrancar. Solución: `_get_materias_activas()` en cada request.

### Tickets BA: Error 500 (columna estado no existe)
Ejecutar `python migrate_ticket_ba_estado.py` antes de usar el código actualizado.

### Obsolescencia — column n.modelo does not exist
Eliminar `n.modelo` de todas las queries en `routes/obsolescencia.py`.

### Secciones del Encargado — Error 500 (column secciones_json does not exist)
`ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS secciones_json TEXT DEFAULT '[]';`

### Formulario de usuario — TemplateSyntaxError: Unexpected end of template
`{% block scripts %}` embebido dentro de `{% block title %}`. Solución: regenerar `form.html` desde cero.

### Espacio Digital: retiro_netbooks.html — block 'content' defined twice
str_replace dejó el contenido original pegado debajo del nuevo. Solución: truncar el archivo en línea 249.

### SyntaxError en mail.py — f-string expression part cannot include a backslash
Python 3.11 no permite `\"` dentro de f-strings. Solución: `pulgadas_str = f' ({tv.pulgadas}")'` como variable previa.

### Config. Sistema — Error 500 al abrir después de agregar templates de TV
Columnas `mail_retiro_tv` y `mail_devolucion_tv` no existen hasta ejecutar `python migrate_mail_tv.py`.
