# SIGA-Tec
## Sistema Integral de Gestión de Recursos Tecnológicos
**E.T. N°7 D.E. 5 — Dolores Lavalle de Lavalle**

---

## 📋 Descripción

SIGA-Tec es un sistema web desarrollado en Flask para gestionar los recursos tecnológicos de la escuela. Permite controlar préstamos de carros de netbooks, el Espacio Digital, pantallas interactivas, control de stock, importación de datos desde Google Drive y generación de reportes en PDF.

---

## ⚙️ Requisitos previos

- Python 3.10 o superior
- Pip
- Cuenta de Google con acceso a Google Cloud Console
- Git (opcional)

---

## 🚀 Instalación local

### 1. Clonar o descargar el proyecto

```bash
git clone https://github.com/N9M8T19/SIGAtec.git
cd SIGAtec_web
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Crear el archivo `.env` en la raíz del proyecto

```
SECRET_KEY=una-clave-secreta-larga-y-dificil
GOOGLE_CLIENT_ID=tu-client-id-de-google
GOOGLE_CLIENT_SECRET=tu-client-secret-de-google
```

### 4. Colocar los archivos de credenciales en la raíz

| Archivo | Descripción |
|---------|-------------|
| `credentials.json` | Credenciales OAuth2 de Gmail (tipo "Aplicación de escritorio") |
| `service_account.json` | Cuenta de servicio para Google Sheets |
| `token.json` | Token de acceso Gmail (se genera automáticamente) |

> ⚠️ Ninguno de estos archivos debe subirse a GitHub. Están incluidos en `.gitignore`.

### 5. Generar el token de Gmail (primera vez)

```bash
python sendMail.py
```

Se abre el navegador, autorizás con la cuenta de la escuela y se genera `token.json`.

### 6. Iniciar el servidor

```bash
python app.py
```

Abrí el navegador en `http://127.0.0.1:5000`

---

## 🔐 Primer acceso

El sistema usa **login con Google**. Para que un usuario pueda entrar:

1. Tiene que tener una cuenta de correo `@bue.edu.ar`
2. El administrador debe cargar ese correo en **Usuarios → editar usuario → Correo Google**

### Usuario administrador por defecto

| Campo | Valor |
|-------|-------|
| Correo Google | nicolas.montefinal@bue.edu.ar |
| Username | admin |
| Rol | Administrador |

---

## 📁 Estructura de carpetas

```
SIGAtec_web/
├── app.py                    # Aplicación principal
├── config.py                 # Configuración
├── models/                   # Modelos de base de datos
├── models_extra/             # Modelos adicionales (horarios, notificaciones)
├── routes/                   # Rutas y lógica de cada módulo
├── services/                 # Servicios (mail, PDF, backup, importación)
├── templates/                # Páginas HTML
├── static/                   # Archivos estáticos (imágenes, CSS)
│   └── img/
│       └── logo_escuela.png  # Logo para PDFs y login
├── backups/                  # Backups automáticos (se crea solo)
├── instance/
│   └── sigartec.db           # Base de datos SQLite
├── .env                      # Variables de entorno (NO subir a GitHub)
├── credentials.json          # Credenciales Gmail (NO subir a GitHub)
├── service_account.json      # Cuenta de servicio (NO subir a GitHub)
├── token.json                # Token Gmail (NO subir a GitHub)
├── sendMail.py               # Script para generar token
├── requirements.txt
├── Procfile
└── render.yaml
```

---

## 🗂️ Módulos del sistema

### Inventario
- **Carros** — ABM de carros de netbooks con listado de equipos
- **Netbooks** — Gestión individual por carro, asignación a alumnos
- **Servicio Técnico** — Lista de netbooks en reparación con detalle del problema
- **Pantallas Digitales** — Pizarrones interactivos fijos en aulas con historial
- **Control de Stock** — Relevamiento físico por carro escaneando códigos de barras
- **Transferir Netbooks** — Mover netbooks de un carro a otro con PDF de informe

### Préstamos
- **Préstamos de Carros** — Registro de retiro y devolución de llaves
- **Espacio Digital** — Préstamo de netbooks individuales a docentes
- **Historial** — Registro completo con filtros por período y fechas personalizadas

### Personas
- **Docentes** — ABM con turno, materia, correo y horarios por módulo
- **Usuarios** — Encargados, directivos y administradores del sistema

### Reportes
- Estadísticas de uso por docente y materia
- PDFs de todos los reportes con logo de la escuela

### Sistema
- **Config. Espacio Digital** — Asignar el carro del Espacio Digital
- **Importar Drive** — Importar datos desde Google Sheets
- **Notificaciones** — Configurar destinatarios de alertas por mail
- **Backups** — Copias de seguridad automáticas y manuales

---

## 📊 Importación desde Google Sheets

### Requisitos
1. Compartir la planilla con la cuenta de servicio:
   `netbook-service@servicios-net-478619.iam.gserviceaccount.com` (permiso: Lector)
2. La hoja de cálculo debe tener el formato correcto

### Formato de planillas

**Netbooks** (una pestaña por carro, ej: "CARRO 10"):
```
Fila 1: COD CARRO         ← encabezado del carro
Fila 2: N° INTERNO | N° DE SERIE   ← encabezados de columnas
Fila 3+: datos de netbooks
```

**Docentes:**
```
Apellido y Nombre | DNI | Email
```

**Pantallas Digitales** (pestaña llamada `PANTALLAS DIGITALES`):
```
AULA | CURSO | NÚMERO DE SERIE
```

---

## 📧 Sistema de notificaciones por mail

El sistema envía mails automáticamente cuando:
- Un docente retira o devuelve un carro
- Un docente retira o devuelve netbooks del Espacio Digital
- Un préstamo supera el tiempo configurado (alerta de demora)
- Un docente termina su módulo sin devolver el material

Para configurar los destinatarios: **Sistema → Notificaciones → Agregar destinatario**

### Si el token de Gmail expira

```bash
python sendMail.py
```

---

## ⏰ Horarios de módulos

Los módulos están configurados para escuela técnica. Para cargar el horario de un docente:

1. Ir a **Docentes**
2. Hacer clic en el ícono 🕐 del docente
3. Agregar los módulos que dicta por día

El sistema bloquea préstamos si el docente intenta pedir fuera de su turno.

---

## 💾 Backups

Los backups se generan automáticamente cada 24 horas y se guardan en la carpeta `backups/`. Se conservan los últimos 30 backups.

Para descargar un backup manual: **Sistema → Backups → Generar y Descargar Backup Ahora**

> ⚠️ Los backups solo funcionan con SQLite (desarrollo local). En producción con PostgreSQL usar el sistema de backup de Render.

---

## 📄 PDFs disponibles

| Reporte | Desde dónde se descarga |
|---------|------------------------|
| Listado general de carros | Carros → botón PDF |
| Netbooks de un carro | Carros → ícono PDF de cada carro |
| Servicio técnico con campo reclamo | Servicio Técnico → botón PDF |
| Historial de préstamos (carros) | Historial → botón PDF |
| Historial Espacio Digital | Historial → botón PDF |
| Estadísticas | Reportes → botón PDF |
| Transferencia de netbooks | Al confirmar una transferencia |
| Control de stock | Control de Stock → resultado → Descargar PDF |

---

## 🚀 Deploy en Render (producción)

### Requisitos adicionales
Agregar al `requirements.txt`:
```
psycopg2-binary==2.9.9
```

### Pasos
1. Crear cuenta en [render.com](https://render.com) con GitHub
2. **New → Blueprint** → conectar repositorio
3. Agregar variables de entorno en Render:
   - `SECRET_KEY`
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`
4. En Google Cloud Console, agregar la URL de Render como redirect URI:
   `https://tu-app.onrender.com/google_auth/google/authorized`

---

## 🛠️ Solución de problemas frecuentes

### Error: `no such column: usuarios.correo`
```bash
python -c "
import sqlite3
conn = sqlite3.connect('instance/sigartec.db')
conn.execute('ALTER TABLE usuarios ADD COLUMN correo VARCHAR(150)')
conn.commit()
conn.close()
print('Listo')
"
```

### Error: `redirect_uri_mismatch` al hacer login con Google
Verificar que en Google Cloud Console → Credenciales → la URL de callback sea exactamente:
```
http://127.0.0.1:5000/google_auth/google/authorized
```

### Error: `Gmail API has not been used`
Habilitar la Gmail API en:
[console.developers.google.com/apis/api/gmail.googleapis.com](https://console.developers.google.com/apis/api/gmail.googleapis.com)

### Las horas se muestran con 3 horas de más
Verificar que `app.py` tenga los filtros Jinja2 de zona horaria Argentina (UTC-3).

### Error al importar desde Drive
Verificar que la planilla esté compartida con:
`netbook-service@servicios-net-478619.iam.gserviceaccount.com`

---

## 📞 Contacto y soporte

**Desarrollado para:** E.T. N°7 D.E. 5 — Dolores Lavalle de Lavalle
**Administrador del sistema:** N. Montefinal Turnes
**Correo:** nicolas.montefinal@bue.edu.ar
