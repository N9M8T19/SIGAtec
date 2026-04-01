# SIGA-Tec — Bitácora del Proyecto
**E.T. N°7 D.E. 5 — Dolores Lavalle de Lavalle**
**Última actualización: 01/04/2026**

---

## 📋 Descripción del sistema

Sistema Integral de Gestión de Recursos Tecnológicos (SIGA-Tec).
Gestiona carros de netbooks, préstamos a docentes, Espacio Digital, pantallas digitales, control de stock, asignación de alumnos por turno, tickets BA Colaborativa e importación desde Google Drive.

- **Framework:** Flask (Python)
- **Base de datos:** SQLite (local) / PostgreSQL (producción)
- **Login:** Google OAuth2 (solo cuentas autorizadas)
- **Deploy:** Railway → en proceso de migración a Render
- **Repo GitHub:** https://github.com/N9M8T19/SIGAtec.git

---

## 🏗️ Estructura del proyecto

```
SIGAtec_web/
├── app.py                          # Factory principal, filtros Jinja2 de hora AR
├── config.py                       # Configuración Flask + Mail
├── models/
│   └── __init__.py                 # Todos los modelos SQLAlchemy
├── models_extra/
│   ├── __init__.py
│   └── horarios_notificaciones.py  # HorarioDocente, ConfigNotificacion, LogNotificacion
├── routes/
│   ├── auth.py                     # Login Google OAuth2
│   ├── carros.py                   # ABM de carros
│   ├── docentes.py                 # ABM de docentes
│   ├── horarios.py                 # Horarios de docentes por módulo
│   ├── importar.py                 # Importación desde Google Sheets
│   ├── main.py                     # Dashboard + Config Espacio Digital
│   ├── netbooks.py                 # ABM de netbooks + asignación alumnos + baja
│   ├── notificaciones.py           # Config de mails + backups
│   ├── pantallas.py                # Pantallas digitales
│   ├── prestamos.py                # Préstamos carros + Espacio Digital + historial
│   ├── reportes.py                 # Estadísticas + PDFs
│   ├── stock.py                    # Control de stock por carro
│   ├── tickets_ba.py               # Tickets BA Colaborativa (NUEVO)
│   ├── transferencias.py           # Transferencia de netbooks entre carros
│   └── usuarios.py                 # ABM de usuarios + Mi Perfil
├── services/
│   ├── __init__.py
│   ├── alertas_horario.py          # Scheduler de alertas por módulo
│   ├── backup.py                   # Backup automático SQLite
│   ├── importar_drive.py           # Lógica de importación Google Sheets
│   ├── mail.py                     # Envío de mails Gmail API OAuth2
│   ├── pdf_reportes.py             # Generación de PDFs de reportes
│   └── pdf_stock.py                # PDF de control de stock
├── templates/
│   ├── auth/login.html
│   ├── backup/index.html
│   ├── carros/
│   │   └── netbooks.html           # Vista de netbooks del carro (con asignación de alumnos)
│   ├── docentes/
│   ├── horarios/
│   ├── importar/
│   │   └── index.html              # Importar carros, docentes, pantallas y alumnos
│   ├── main/
│   │   ├── dashboard.html
│   │   └── config_espacio_digital.html
│   ├── netbooks/
│   │   └── servicio_tecnico.html   # Lista de netbooks en servicio técnico
│   ├── notificaciones/
│   ├── pantallas/
│   ├── prestamos/
│   ├── reportes/
│   ├── stock/
│   ├── tickets_ba/
│   │   └── index.html              # Tickets BA Colaborativa (NUEVO)
│   ├── transferencias/
│   ├── usuarios/
│   └── base.html                   # Layout principal con sidebar
├── static/
│   └── img/
│       └── logo_escuela.png
├── migrate_alumnos.py              # Migración: tabla alumnos + columnas turno
├── migrate_baja_netbook.py         # Migración: campos baja en netbooks
├── migrate_reclamo.py              # Migración: campo nro_reclamo en netbooks
├── credentials.json                # Credenciales Google (NO subir a GitHub)
├── service_account.json            # Cuenta de servicio Google (NO subir a GitHub)
├── token.json                      # Token OAuth Gmail (NO subir a GitHub)
├── sendMail.py                     # Script para generar/renovar token OAuth
├── .env                            # Variables de entorno (NO subir a GitHub)
├── .gitignore
├── Procfile
├── render.yaml
└── requirements.txt
```

---

## 🗄️ Modelos de base de datos

### `models/__init__.py`

| Modelo | Tabla | Descripción |
|--------|-------|-------------|
| `Usuario` | `usuarios` | Encargados, directivos, admin. Login por correo Google |
| `Docente` | `docentes` | Docentes con turno, materia, correo |
| `Carro` | `carros` | Carros de netbooks |
| `Alumno` | `alumnos` | Alumnos con curso y turno (M/T) |
| `Netbook` | `netbooks` | Netbooks con FK a carro, alumno_manana, alumno_tarde |
| `PrestamoCarro` | `prestamos_carros` | Préstamos de llaves/carros |
| `PrestamoNetbook` | `prestamos_netbooks` | Préstamos del Espacio Digital |
| `PrestamoNetbookItem` | `prestamo_netbook_items` | Items de cada préstamo netbook |
| `ConfigEspacioDigital` | `config_espacio_digital` | Carro asignado al Espacio Digital |
| `PantallaDigital` | `pantallas_digitales` | Pizarrones interactivos fijos en aulas |
| `HistorialPantalla` | `historial_pantallas` | Historial de eventos de pantallas |
| `TicketBA` | `tickets_ba` | Tickets de reclamo BA Colaborativa |
| `TicketBANetbook` | `tickets_ba_netbooks` | Netbooks vinculadas a cada ticket |

### `models_extra/horarios_notificaciones.py`

| Modelo | Descripción |
|--------|-------------|
| `HorarioDocente` | Módulos por día para cada docente |
| `ConfigNotificacion` | Destinatarios de mails con eventos configurables |
| `LogNotificacion` | Log de notificaciones enviadas |

### ⚠️ Columnas agregadas manualmente (migraciones)

```bash
python migrate_alumnos.py        # Crea tabla alumnos + columnas alumno_manana_id, alumno_tarde_id en netbooks
python migrate_baja_netbook.py   # Agrega motivo_baja, fecha_baja, usuario_baja en netbooks
python migrate_reclamo.py        # Agrega nro_reclamo en netbooks
```

Las tablas `tickets_ba` y `tickets_ba_netbooks` se crean automáticamente con `db.create_all()` al iniciar Flask.

---

## 🔐 Autenticación

- **Login:** Solo Google OAuth2
- **Credencial OAuth web:** en Google Cloud Console, proyecto `servicios-net-478619`
- **Scopes:** email, profile, userinfo
- **Callback local:** `http://127.0.0.1:5000/google_auth/google/authorized`
- **Callback producción:** agregar URL de Render cuando se deploje
- **Control de acceso:** el correo del usuario debe coincidir con `Usuario.correo` en la BD

### Roles y permisos

| Rol | Permisos |
|-----|----------|
| `Encargado` | Solo préstamos |
| `Directivo` | Todo igual que Administrador |
| `Administrador` | Todo |

---

## 📧 Sistema de mails

- **API:** Gmail API con OAuth2 (cuenta `det_7_de5@bue.edu.ar`)
- **Credenciales:** `credentials.json` (tipo "Aplicación de escritorio")
- **Token:** `token.json` (generado con `python sendMail.py`)
- **Scopes:** `gmail.send` + `spreadsheets.readonly`
- **Eventos notificados:** retiro/devolución de carros, retiro/devolución de netbooks, alertas de demora, alertas de horario

### ⚠️ Si el token expira
```bash
python sendMail.py
```
Autorizar en el navegador → genera nuevo `token.json`

---

## 📊 Importación desde Google Drive

- **Método:** Google Sheets API con cuenta de servicio
- **Archivo:** `service_account.json`
- **Cuenta:** `netbook-service@servicios-net-478619.iam.gserviceaccount.com`
- **Requisito:** compartir cada planilla con esa cuenta como "Lector"

### Formato de planillas

**Netbooks** (una pestaña por carro, ej: "CARRO 10"):
- Fila 1: `COD CARRO` (encabezado del carro)
- Fila 2: `N° INTERNO` | `N° DE SERIE` (encabezados)
- Fila 3+: datos

**Docentes:**
- `Apellido y Nombre` | `DNI` | `Email`

**Alumnos** (una pestaña por curso + turno):
- Nombre de pestaña: `N1G1 M` (mañana) o `N1G1 T` (tarde)
- Columnas: `Apellido y Nombre` | `DNI`
- El turno se detecta automáticamente por el sufijo de la pestaña

**Pantallas Digitales** (pestaña: `PANTALLAS DIGITALES`):
- `AULA` | `CURSO` | `NÚMERO DE SERIE`

---

## 👨‍🎓 Asignación de alumnos a netbooks

Cada netbook puede tener dos alumnos asignados simultáneamente: uno de turno mañana y uno de turno tarde.

- **Importar alumnos:** Sistema → Importar Drive → tarjeta "Alumnos"
- **Asignar:** Carros → entrar al carro → ícono ☀️ (mañana) o 🌙 (tarde) en cada fila
- **Desasignar:** ícono 👤- del turno correspondiente
- El buscador del modal filtra automáticamente por turno

---

## 🔧 Servicio Técnico

- Desde la vista del carro, el ícono 🔧 abre un modal que **pide el motivo obligatorio** antes de enviar al servicio
- El motivo queda guardado en el campo `problema` de la netbook
- Desde la pantalla de Servicio Técnico: búsqueda por N° interno, N° serie o carro; botón "Reparada" vuelve a la misma pantalla
- El PDF de servicio técnico muestra: Carro, Aula, N° Interno, N° Serie, Problema

---

## 🎟️ Tickets BA Colaborativa

Nueva sección en el menú lateral (Inventario → Tickets BA Colaborativa).

- Permite crear tickets vinculados a las netbooks que están en servicio técnico
- Campos: N° de reclamo BA, quién lo registró (usuario logueado), fecha, observaciones, netbooks incluidas
- PDF por ticket individual o de todos los tickets
- Las tablas se crean automáticamente al iniciar Flask

---

## 📄 PDFs disponibles

| PDF | Ruta |
|-----|------|
| Listado de carros | `/reportes/pdf/carros` |
| Netbooks de un carro | `/reportes/pdf/carro/<id>` |
| Inventario de netbooks (N° interno + serie) | `/reportes/pdf/inventario/carro/<id>` |
| Asignación de alumnos por carro | `/reportes/pdf/asignaciones/carro/<id>` |
| Asignación de una netbook | `/reportes/pdf/asignaciones/netbook/<id>` |
| Servicio técnico | `/reportes/pdf/servicio-tecnico` |
| Historial carros (con fechas) | `/reportes/pdf/historial-carros?periodo=hoy` |
| Historial Espacio Digital | `/reportes/pdf/historial-netbooks?periodo=semana` |
| Estadísticas | `/reportes/pdf/estadisticas` |
| Transferencia de netbooks | Generado al confirmar transferencia |
| Control de stock | `/stock/pdf/<carro_id>` |
| Baja de netbook | Generado al confirmar la baja (descarga automática) |
| Tickets BA Colaborativa (todos) | `/tickets-ba/pdf` |
| Ticket BA individual | `/tickets-ba/<id>/pdf` |

---

## ⏰ Zona horaria

- La BD guarda en **UTC**
- La app muestra en **Argentina (UTC-3)**
- Filtros Jinja2 disponibles:
  - `{{ fecha|arg_datetime }}` → `dd/mm/YYYY HH:MM`
  - `{{ fecha|arg_time }}` → `HH:MM`
  - `{{ fecha|arg_date }}` → `dd/mm`

---

## 🔧 Variables de entorno (.env)

```
SECRET_KEY=tu-clave-secreta
GOOGLE_CLIENT_ID=tu-client-id-oauth-web
GOOGLE_CLIENT_SECRET=tu-client-secret-oauth-web
```

---

## 📦 Requirements actuales

```
Flask==2.3.3
Flask-SQLAlchemy==3.0.5
Flask-Login==0.6.2
Flask-WTF==1.1.1
Werkzeug==2.3.7
SQLAlchemy==1.4.50
WTForms==3.0.1
reportlab==4.0.8
gunicorn==21.2.0
python-dotenv==1.0.0
google-auth==2.29.0
google-auth-oauthlib==1.2.0
google-api-python-client==2.126.0
flask-dance==7.0.1
```

> **Nota:** `psycopg2-binary` solo para producción (Render con PostgreSQL)

---

## ✅ Funcionalidades completadas

- [x] Login con Google OAuth2 (lista fija de mails autorizados)
- [x] ABM de carros, netbooks, docentes, usuarios
- [x] Préstamos de carros con control de turno del docente
- [x] Espacio Digital (préstamo de netbooks individuales)
- [x] Historial con filtros por período y fechas personalizadas
- [x] Horarios de docentes por módulo (16 módulos configurables)
- [x] Notificaciones por mail (retiro/devolución/alertas)
- [x] Alertas automáticas por fin de módulo y por demora
- [x] Backup automático SQLite (cada 24hs) + descarga manual
- [x] Pantallas digitales con historial
- [x] Control de stock por carro (escaneo + comparación)
- [x] Transferencia de netbooks entre carros + PDF
- [x] Importación desde Google Sheets por pestaña
- [x] PDFs de todos los reportes con logo de escuela
- [x] Zona horaria Argentina (UTC-3) en toda la app
- [x] Mi Perfil (editar nombre, apellido, username)
- [x] Asignación de carro al Espacio Digital
- [x] Control de turno en préstamos
- [x] Asignación de alumnos a netbooks por turno (mañana/tarde)
- [x] Importación de alumnos desde Google Sheets (pestaña = curso + turno)
- [x] PDF de asignaciones por carro y por netbook individual
- [x] PDF Inventario simple (N° interno + N° serie) por carro
- [x] Dar de baja netbooks con motivo + PDF de constancia (borra el registro)
- [x] Servicio técnico con motivo obligatorio al enviar
- [x] Servicio técnico: búsqueda + no vuelve al inicio al marcar reparada
- [x] Tickets BA Colaborativa: crear, listar, vincular netbooks, PDF por ticket y general

## 🔄 Pendiente / En desarrollo

- [ ] Colores del escudo de la escuela en toda la página
- [ ] Títulos de página en mayúscula (en progreso)
- [ ] Corregir horarios de módulos de la escuela (pendiente confirmar horarios reales)
- [ ] Escanear código de barras al agregar netbook

---

## 🚀 Deploy en Render (pendiente)

1. Crear cuenta en render.com con GitHub
2. New → Blueprint → conectar repositorio
3. Agregar variables de entorno: `SECRET_KEY`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`
4. Agregar `psycopg2-binary` al `requirements.txt`
5. Agregar URL de Render en Google Cloud Console como redirect URI

---

## 👤 Usuario administrador

- **DNI:** 41469656
- **Username:** admin
- **Nombre:** N.Montefinal Turnes
- **Correo Google:** nicolas.montefinal@bue.edu.ar
- **Rol:** Administrador
