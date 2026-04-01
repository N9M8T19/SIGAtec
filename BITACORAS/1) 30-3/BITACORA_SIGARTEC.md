# SIGA-Tec — Bitácora del Proyecto
**E.T. N°7 D.E. 5 — Dolores Lavalle de Lavalle**
**Última actualización: 30/03/2026**

---

## 📋 Descripción del sistema

Sistema Integral de Gestión de Recursos Tecnológicos (SIGA-Tec).
Gestiona carros de netbooks, préstamos a docentes, Espacio Digital, pantallas digitales, control de stock e importación desde Google Drive.

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
│   ├── netbooks.py                 # ABM de netbooks
│   ├── notificaciones.py           # Config de mails + backups
│   ├── pantallas.py                # Pantallas digitales
│   ├── prestamos.py                # Préstamos carros + Espacio Digital + historial
│   ├── reportes.py                 # Estadísticas + PDFs
│   ├── stock.py                    # Control de stock por carro
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
│   ├── auth/login.html             # Login solo con Google
│   ├── backup/index.html
│   ├── carros/
│   ├── docentes/
│   ├── horarios/
│   ├── importar/
│   ├── main/
│   │   ├── dashboard.html
│   │   └── config_espacio_digital.html
│   ├── netbooks/
│   ├── notificaciones/
│   ├── pantallas/
│   ├── prestamos/
│   ├── reportes/
│   ├── stock/
│   ├── transferencias/
│   ├── usuarios/
│   └── base.html                   # Layout principal con sidebar
├── static/
│   └── img/
│       └── logo_escuela.png        # Logo para PDFs y login
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
| `Netbook` | `netbooks` | Netbooks individuales con FK a carro |
| `PrestamoCarro` | `prestamos_carros` | Préstamos de llaves/carros |
| `PrestamoNetbook` | `prestamos_netbooks` | Préstamos del Espacio Digital |
| `PrestamoNetbookItem` | `prestamo_netbook_items` | Items de cada préstamo netbook |
| `ConfigEspacioDigital` | `config_espacio_digital` | Carro asignado al Espacio Digital |
| `PantallaDigital` | `pantallas_digitales` | Pizarrones interactivos fijos en aulas |
| `HistorialPantalla` | `historial_pantallas` | Historial de eventos de pantallas |

### `models_extra/horarios_notificaciones.py`

| Modelo | Descripción |
|--------|-------------|
| `HorarioDocente` | Módulos por día para cada docente |
| `ConfigNotificacion` | Destinatarios de mails con eventos configurables |
| `LogNotificacion` | Log de notificaciones enviadas |

### ⚠️ Columna importante agregada manualmente

La columna `correo` en la tabla `usuarios` fue agregada con:
```sql
ALTER TABLE usuarios ADD COLUMN correo VARCHAR(150);
```

La relación en `ConfigEspacioDigital` debe tener:
```python
carro = db.relationship('Carro', foreign_keys=[carro_id])
```

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

**Alumnos:**
- `Apellido y Nombre` | `DNI`

**Pantallas Digitales** (pestaña: `PANTALLAS DIGITALES`):
- `AULA` | `CURSO` | `NÚMERO DE SERIE`

---

## ⏰ Zona horaria

- La BD guarda en **UTC**
- La app muestra en **Argentina (UTC-3)**
- Filtros Jinja2 disponibles:
  - `{{ fecha|arg_datetime }}` → `dd/mm/YYYY HH:MM`
  - `{{ fecha|arg_time }}` → `HH:MM`
  - `{{ fecha|arg_date }}` → `dd/mm`

---

## 📄 PDFs disponibles

| PDF | Ruta |
|-----|------|
| Listado de carros | `/reportes/pdf/carros` |
| Netbooks de un carro | `/reportes/pdf/carro/<id>` |
| Netbooks asignadas a alumnos | `/reportes/pdf/asignadas` |
| Servicio técnico + campo reclamo Mi BA | `/reportes/pdf/servicio-tecnico` |
| Historial carros (con fechas) | `/reportes/pdf/historial-carros?periodo=hoy` |
| Historial Espacio Digital | `/reportes/pdf/historial-netbooks?periodo=semana` |
| Estadísticas | `/reportes/pdf/estadisticas` |
| Transferencia de netbooks | Generado al confirmar transferencia |
| Control de stock | `/stock/pdf/<carro_id>` |

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
- [x] PDF servicio técnico con campo número de reclamo Mi BA
- [x] Zona horaria Argentina (UTC-3) en toda la app
- [x] Mi Perfil (editar nombre, apellido, username)
- [x] Asignación de carro al Espacio Digital
- [x] Control de turno en préstamos

## 🔄 Pendiente / En desarrollo

- [ ] Asignación de netbooks a dos alumnos (mañana/tarde) + PDF
- [ ] Dar de baja netbooks desde el carro con motivo + PDF
- [ ] Servicio técnico: búsqueda + no volver al inicio al sacar
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
