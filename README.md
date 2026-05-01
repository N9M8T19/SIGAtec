# SIGA-Tec
## Sistema Integral de Gestión de Recursos Tecnológicos
**E.T. N°7 D.E. 5 — Dolores Lavalle de Lavalle**

---

## 📋 Descripción

SIGA-Tec es un sistema web desarrollado en Flask para gestionar los recursos tecnológicos de la escuela. Permite controlar préstamos de carros de netbooks, el Espacio Digital, pantallas interactivas, televisores, asignación de alumnos por turno, tickets de reclamo BA Colaborativa, control de stock, mensajería interna entre el equipo, registro de obsolescencia y reemplazos de netbooks, importación de datos desde Google Drive y generación de reportes en PDF.

---

## ⚙️ Requisitos previos

- Python 3.11 o superior
- Pip
- Cuenta de Google con acceso a Google Cloud Console
- Git

---

## 🚀 Instalación local

### 1. Clonar el proyecto

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
GMAIL_USER=aulamagnaespaciodigital@gmail.com
GMAIL_APP_PASSWORD=tu-app-password-de-16-caracteres
```

### 4. Colocar los archivos de credenciales en la raíz

| Archivo | Descripción |
|---------|-------------|
| `credentials.json` | Credenciales OAuth2 de Gmail (tipo "Aplicación de escritorio") |
| `service_account.json` | Cuenta de servicio para Google Sheets |
| `token.json` | Token de acceso Gmail (se genera automáticamente) |

> ⚠️ Ninguno de estos archivos debe subirse a GitHub. Están incluidos en `.gitignore`.

### 5. Colocar los logos en `static/img/`

| Archivo | Uso |
|---------|-----|
| `static/img/logo_escuela.png` | Escudo de la escuela — aparece en PDFs |
| `static/img/logo_SIGA-tec.png` | Logo del sistema — aparece en la pantalla de login |

### 6. Ejecutar las migraciones de base de datos

```bash
python migrate_alumnos.py
python migrate_baja_netbook.py
python migrate_reclamo.py
python migrate_netbook_alumno.py
python migrate_impresoras3d.py
python migrate_estado_carro.py
python migrate_sesiones.py
python migrate_config_espacio_digital_2.py
python migrate_ticket_ba_carro.py
python migrate_asignaciones_internas.py
python migrate_tvs.py
python migrate_materia_prestamo.py
python migrate_config_sistema.py
python migrate_mensajeria.py
python migrate_ticket_ba_estado.py
python migrate_obsolescencia.py
python migrate_secciones_encargado.py
python migrate_secciones_usuario.py
python migrate_mail_tv.py
```

### 7. Generar el token de Gmail (primera vez)

```bash
python sendMail.py
```

### 8. Iniciar el servidor

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

## 🎨 Identidad visual

**Pantalla de login** — colores del logo SIGA-Tec:
- Azul marino `#1e3a6e` + Verde `#2ebd4e`

**App (dentro del sistema)** — colores del escudo de la escuela:
- Azul marino oscuro `#1a2a6c` (sidebar y headers)
- Naranja `#e8821a` (acento — la llama del escudo)
- Todos los títulos en **MAYÚSCULA**

---

## 📁 Estructura de carpetas

```
SIGAtec_web/
├── app.py                          # ⚠️ Actualizado 30/04/2026 — registra obsolescencia_bp
│                                   # ⚠️ Actualizado 29/04/2026 — registra mensajeria_bp
│                                   # ⚠️ Actualizado 27/04/2026 — registra tvs_bp, asignaciones_bp; elimina ubicaciones_bp
├── config.py
├── models/
│   ├── __init__.py                 # ⚠️ Actualizado 29/04/2026 — TicketBA: campos estado/fecha_cierre/motivo_cierre/cerrado_por
│   │                               # ⚠️ Actualizado 29/04/2026 — modelos Mensaje y MensajeLeid (mensajería interna)
│   │                               # ⚠️ Actualizado 28/04/2026 — PrestamoCarro: campo materia_prestamo
│   │                               # ⚠️ Actualizado 27/04/2026 — modelos TV y PrestamoTV
│   │                               # ⚠️ Actualizado 24/04/2026 — AsignacionInterna
│   │                               # ⚠️ Actualizado 22/04/2026 — TicketBANetbook: carro_id
│   │                               # ⚠️ Actualizado 20/04/2026 — ConfigEspacioDigital: carro_id_2
│   │                               # ⚠️ Actualizado 15/04/2026 — Carro: estado/motivo_servicio/fecha_servicio
│   └── sesion.py                   # ⚠️ Nuevo 16/04/2026 — modelo SesionEncargado
├── models_extra/
│   └── horarios_notificaciones.py
├── routes/
│   ├── auth.py                     # ⚠️ Actualizado 16/04/2026 — registra sesión al login/logout
│   ├── asignaciones.py             # ⚠️ Nuevo 24/04/2026 — ABM Asignaciones Internas (solo Directivo/Admin)
│   ├── carros.py                   # ⚠️ Actualizado 28/04/2026 — netbooks() y asignar_automatico() ordenan por numero_interno numérico
│   │                               # ⚠️ Actualizado 15/04/2026 — enviar_servicio y recuperar_carro
│   ├── docentes.py                 # ⚠️ Actualizado 29/04/2026 — usa _get_materias_activas() en nuevo() y editar()
│   │                               # ⚠️ Actualizado 15/04/2026 — fix IntegrityError préstamos históricos
│   ├── etiquetas.py                # ⚠️ Actualizado 27/04/2026 — endpoints para TVs, Pantallas e Impresoras 3D
│   ├── netbooks.py                 # ⚠️ Actualizado 28/04/2026 — validación número interno duplicado por carro
│   │                               # ⚠️ Actualizado 28/04/2026 — nuevo endpoint GET /netbooks/verificar-numero-interno (AJAX)
│   │                               # ⚠️ Actualizado 28/04/2026 — servicio_tecnico() ordena por numero_interno numérico
│   │                               # ⚠️ Actualizado 20/04/2026 — validación número de serie duplicado en alta y edición
│   ├── obsolescencia.py            # ⚠️ Nuevo 30/04/2026 — ABM obsolescencia + reemplazos + pendientes de asignación
│   ├── prestamos.py                # ⚠️ Actualizado 28/04/2026 — retiro_carro() guarda materia_prestamo del módulo actual
│   │                               # ⚠️ Actualizado 27/04/2026 — carros() pasa tvs_prestadas al template
│   │                               # ⚠️ Actualizado 20/04/2026 — espacio digital y retiro soportan 2 carros
│   │                               # ⚠️ Actualizado 16/04/2026 — endpoints alerta_pdf_carro y alerta_pdf_netbooks
│   ├── sesiones.py                 # ⚠️ Nuevo 16/04/2026 — listado y cierre de sesiones de encargados
│   ├── stock.py                    # ⚠️ Actualizado 24/04/2026 — _procesar_control_masivo() incluye asignaciones internas
│   │                               # ⚠️ Actualizado 22/04/2026 — control masivo + fix PDF session
│   ├── tickets_ba.py               # ⚠️ Actualizado 29/04/2026 — cerrar()/reabrir() en lugar de eliminar() para tickets activos
│   │                               # ⚠️ Actualizado 22/04/2026 — soporta carros en servicio + carro_ids en nuevo()
│   ├── transferencias.py           # ⚠️ Actualizado 15/04/2026 — acepta carro_origen_id precargado
│   ├── tvs.py                      # ⚠️ Nuevo 27/04/2026 — ABM + préstamos + historial + etiquetas de TVs
│   ├── mensajeria.py               # ⚠️ Nuevo 29/04/2026 — chat interno: 4 canales, avisos rápidos, polling, badges no leídos
│   ├── alumnos.py
│   ├── main.py                     # ⚠️ Actualizado 28/04/2026 — /estadisticas agrega top_docentes y top_materias por materia_prestamo
│   │                               # ⚠️ Actualizado 28/04/2026 — nueva ruta GET /estadisticas (solo Directivo/Admin)
│   │                               # ⚠️ Actualizado 27/04/2026 — novedades TVs + stats dashboard
│   │                               # ⚠️ Actualizado 22/04/2026 — novedades del día incluye servicio técnico
│   ├── horarios.py                 # ⚠️ Actualizado 21/04/2026 — endpoint PDF horario docente
│   ├── importar.py                 # ⚠️ Actualizado 21/04/2026 — importar horarios vía Excel o Google Sheets
│   └── impresoras3d.py             # ABM Impresoras 3D — nuevo 14/04/2026
├── services/
│   ├── mail.py
│   ├── importar_drive.py           # ⚠️ Actualizado 28/04/2026 — fix normalización horarios Excel + acumulación módulos
│   │                               # ⚠️ Actualizado 21/04/2026 — importar_horarios_docentes() vía Google Sheets
│   └── pdf_reportes.py             # ⚠️ Actualizado 28/04/2026 — pdf_estadisticas() muestra materia discriminada por módulo
│                                   # ⚠️ Actualizado 27/04/2026 — pdf_historial_tvs() + pdf_etiquetas_tvs()
│                                   # ⚠️ Actualizado 22/04/2026 — pdf_control_masivo_stock(): landscape, 3 secciones
│                                   # ⚠️ Actualizado 21/04/2026 — pdf_horario_docente(): landscape, carro asignado
│                                   # ⚠️ Actualizado 20/04/2026 — historial landscape + Autorizó Retiro/Devolución
│                                   # ⚠️ Actualizado 16/04/2026 — pdf_alerta_demora_carro y pdf_alerta_demora_netbooks
├── templates/
│   ├── base.html                   # ⚠️ Actualizado 30/04/2026 — link Obsolescencia en sidebar (todos los roles)
│   │                               # ⚠️ Actualizado 29/04/2026 — link Mensajería + badge no leídos en sidebar
│   │                               # ⚠️ Actualizado 28/04/2026 — link Estadísticas en sidebar (solo Directivo/Admin)
│   │                               # ⚠️ Actualizado 27/04/2026 — link Televisores en Inventario y Préstamos; elimina Ubicaciones
│   │                               # ⚠️ Actualizado 24/04/2026 — link Asignaciones Internas (solo Directivo/Admin)
│   │                               # ⚠️ Actualizado 22/04/2026 — link Stock Masivo en sidebar fijo y peek
│   ├── obsolescencia/              # ⚠️ Nuevo 30/04/2026
│   │   ├── index.html              # Listado con filtros + badge pendientes + modal asignar carro
│   │   ├── nueva.html              # Alta de netbook obsoleta — selector carro/netbook + motivo
│   │   └── reemplazo.html          # Registro de equipo nuevo — asignar a carro o dejar pendiente
│   ├── main/
│   │   └── estadisticas.html       # ⚠️ Nuevo 28/04/2026 — Estadísticas: tarjetas resumen + ranking carros + top docentes + top materias
│   ├── asignaciones/               # ⚠️ Nuevo 24/04/2026
│   │   ├── index.html
│   │   └── form.html
│   ├── etiquetas/
│   │   ├── index.html              # ⚠️ Actualizado 27/04/2026 — accesos a TVs, Pantallas e Impresoras
│   │   ├── tvs.html                # ⚠️ Nuevo 27/04/2026
│   │   ├── pantallas.html          # ⚠️ Nuevo 27/04/2026
│   │   └── impresoras.html         # ⚠️ Nuevo 27/04/2026
│   ├── tvs/                        # ⚠️ Nuevo 27/04/2026
│   │   ├── index.html
│   │   ├── form.html
│   │   ├── prestar.html            # ⚠️ Actualizado 29/04/2026 — buscador de docente con autocomplete
│   │   ├── devolver.html
│   │   ├── prestamos.html
│   │   └── historial.html
│   ├── horarios/
│   │   └── ver_docente.html        # ⚠️ Actualizado 21/04/2026 — botón PDF Horario (naranja)
│   ├── importar/
│   │   └── horarios_docentes.html  # ⚠️ Actualizado 28/04/2026 — aviso acumulación módulos + instrucciones docentes turno Varios
│   ├── carros/
│   │   └── index.html              # ⚠️ Actualizado 15/04/2026 — badge estado, modal servicio, acciones en una fila
│   ├── netbooks/
│   │   ├── servicio_tecnico.html   # ⚠️ Actualizado 15/04/2026 — pantalla unificada carros + netbooks
│   │   └── form.html               # ⚠️ Actualizado 28/04/2026 — campo numero_interno tipo number + alerta AJAX duplicado
│   ├── sesiones/                   # ⚠️ Nuevo 16/04/2026
│   │   └── index.html
│   ├── stock/
│   │   ├── index.html
│   │   ├── relevar.html
│   │   ├── resultado.html
│   │   └── control_masivo.html     # ⚠️ Nuevo 22/04/2026 — control masivo con estética del sistema
│   ├── docentes/
│   ├── alumnos/
│   ├── impresoras3d/
│   ├── mensajeria/                 # ⚠️ Nuevo 29/04/2026
│   │   └── index.html              # Chat tipo burbuja — 4 canales + avisos rápidos + polling
│   └── prestamos/
│       ├── carros.html             # ⚠️ Actualizado 27/04/2026 — sección TVs prestadas
│       │                           # ⚠️ Actualizado 16/04/2026 — botón Parte PDF en filas con demora >= 120 min
│       ├── espacio_digital.html    # ⚠️ Actualizado 20/04/2026 — info panel muestra ambos carros configurados
│       ├── historial.html          # ⚠️ Actualizado 20/04/2026 — columnas Autorizó Retiro y Autorizó Devolución
│       └── retiro_netbooks.html    # ⚠️ Actualizado 20/04/2026 — netbooks agrupadas por carro + botones selección rápida
├── templates/tickets_ba/
│   └── index.html                  # ⚠️ Actualizado 29/04/2026 — sección resueltos colapsable + modal cierre + botón reabrir
│                                   # ⚠️ Actualizado 22/04/2026 — sección carros en servicio con checkbox por carro
├── migrate_obsolescencia.py        # ⚠️ Nuevo 30/04/2026 — crea tabla obsolescencias (psycopg2 directo)
├── migrate_ticket_ba_estado.py     # ⚠️ Nuevo 29/04/2026 — agrega estado/fecha_cierre/motivo_cierre/cerrado_por a tickets_ba
├── migrate_materia_prestamo.py     # ⚠️ Nuevo 28/04/2026 — agrega columna materia_prestamo a prestamos_carros
├── migrate_mensajeria.py           # ⚠️ Nuevo 29/04/2026 — crea tablas mensajes y mensajes_leidos
├── migrate_tvs.py                  # ⚠️ Nuevo 27/04/2026 — crea tablas tvs y prestamos_tvs
├── migrate_asignaciones_internas.py # ⚠️ Nuevo 24/04/2026 — psycopg2 directo, DROP + CREATE
├── migrate_ticket_ba_carro.py      # ⚠️ Nuevo 22/04/2026
├── migrate_config_espacio_digital_2.py
├── migrate_estado_carro.py         # ⚠️ Nuevo 15/04/2026
├── migrate_sesiones.py             # ⚠️ Nuevo 16/04/2026
├── migrate_impresoras3d.py
├── migrate_alumnos.py
├── migrate_baja_netbook.py
├── migrate_reclamo.py
├── migrate_netbook_alumno.py
├── requirements.txt
├── Procfile
├── render.yaml
└── .python-version
```

---

## 🗂️ Módulos del sistema

### Dashboard
- **Sidebar colapsable** — botón ☰ en el header. Al colapsar, acercar el mouse al borde izquierdo muestra el menú flotante. El estado se recuerda entre sesiones.
- **Novedades del día** — panel con los últimos retiros, devoluciones, tickets y eventos de servicio técnico del día, incluyendo préstamos y devoluciones de TVs y **netbooks nuevas pendientes de asignación a carro** (filtrado por hora Argentina)
- **Búsqueda global** — encuentra carros, netbooks y alumnos desde cualquier pantalla

### 💬 Mensajería Interna
Accesible desde el sidebar por todos los roles (Encargado, Directivo y Administrador). Permite comunicación interna en tiempo real entre el equipo sin salir del sistema.

- **4 canales:** General, Servicio Técnico, Préstamos, Avisos
- **Chat tipo burbuja** — mensajes propios en azul marino a la derecha, mensajes ajenos a la izquierda con nombre y rol destacado (Administrador en rojo, Directivo en violeta, Encargado en azul)
- **Tipos de mensaje:** `normal` (azul) y `aviso` (naranja, con ícono de megáfono)
- **Avisos rápidos** — botones predefinidos por canal para enviar mensajes frecuentes con un clic (ej: "🔧 Carro enviado a servicio técnico", "⏰ Préstamo con demora")
- **Polling automático** cada 8 segundos — los mensajes nuevos aparecen sin recargar la página
- **Badge de no leídos** en el link del sidebar, actualizado cada 15 segundos en todas las páginas del sistema
- **Enter para enviar**, Shift+Enter para nueva línea

### Inventario
- **Carros** — ABM de carros de netbooks. Badge de estado (verde/naranja). Botón 🔧 para enviar el carro físico a servicio técnico con selector de motivo. Botón ✅ para recuperarlo.
- **Netbooks** — Gestión individual, asignación a alumnos, baja con PDF, servicio técnico. El número de serie y el número interno se validan en tiempo real al crear o editar. No se pueden repetir números internos dentro del mismo carro.
- **Servicio Técnico** — Pantalla unificada: carros físicos en servicio + netbooks en servicio. Buscador global + PDF con las dos secciones.
- **Pantallas Digitales** — Pizarrones interactivos con historial
- **Impresoras 3D** — ABM con número interno, modelo, N° de serie, aula y estado
- **Televisores** — ABM completo. Código TV-01, marca, modelo, pulgadas, N° de serie, aula por defecto Aula Magna. Checklist de componentes incluidos. Servicio técnico con modal igual que carros.
- **Obsolescencia y Reemplazos** — Registro de netbooks obsoletas o irreparables con trazabilidad completa del reemplazo. Ver sección dedicada más abajo.
- **Control de Stock** — Relevamiento físico por carro: escaneo o ingreso manual de números de serie, comparación contra el sistema, PDF del resultado.
- **Stock Masivo** — Control masivo de todas las computadoras de la escuela. Cruza un listado externo contra todos los carros y asignaciones internas. PDF landscape con 3 secciones.
- **Transferir Netbooks** — Mover netbooks entre carros con PDF. El carro origen queda preseleccionado al venir desde servicio técnico.
- **Tickets BA Colaborativa** — Reclamos vinculados a netbooks individuales o carros completos en servicio. Los tickets se **archivan como resueltos** en lugar de eliminarse — quedan disponibles en la sección de resueltos y se pueden reabrir si el problema reaparece.
- **Asignaciones Internas** — Registro de netbooks asignadas permanentemente a un docente o área (dirección, preceptoría, biblioteca). Solo visible para Directivo y Administrador. Los equipos participan en el cruce del Stock Masivo y se suman al total del dashboard.

### Préstamos
- **Préstamos de Carros** — Retiro y devolución de llaves. Los carros prestados y en servicio aparecen bloqueados. Botón Parte PDF cuando el préstamo supera 2 horas. Debajo de la tabla muestra también las **TVs prestadas activas**. Al registrar el retiro, el sistema detecta automáticamente la materia del módulo horario actual del docente y la guarda en el préstamo.
- **Espacio Digital** — Préstamo de netbooks individuales. Soporta hasta 2 carros simultáneos.
- **Televisores** — Acceso directo desde el sidebar. Muestra préstamos activos + grilla de estado de todas las TVs con botón **Prestar** directo en las disponibles. El préstamo es solo a docentes (obligatorio) — el formulario usa el mismo buscador con autocomplete que el retiro de carro (busca por apellido o DNI). La devolución incluye checklist de componentes. Historial con PDF landscape. **Al registrar el retiro y la devolución se envía un mail automático al docente** (template configurable desde Config. Sistema).
- **Historial** — Registro completo con filtros. Soporta filtro por rango horario (`hora_desde` / `hora_hasta`). Muestra quién autorizó el retiro y la devolución. PDF landscape.

### Etiquetas
Accesible desde **Inventario → Etiquetas**. Permite seleccionar equipos por card y generar etiquetas adhesivas con código de barras para imprimir en A4, igual que las de netbooks.
- **Netbooks** — grilla por carro con filtro y búsqueda
- **Televisores** — cards con código TV-01, marca, modelo, aula
- **Pantallas Digitales** — cards con código PD-01
- **Impresoras 3D** — cards con código IMP-01

### Personas
- **Docentes** — ABM con buscador en tiempo real. Baja con selector de motivo (jubilación elimina permanentemente). El selector de materia/cargo en el formulario de alta/edición lee `ConfigSistema` en runtime — los cargos agregados desde Config. Sistema aparecen de inmediato.
- **Alumnos** — Listado paginado (50 por página), filtros por curso y turno, importación desde Drive
- **Usuarios** — Encargados, directivos y administradores

### Reportes
- PDFs de todos los reportes con logo de la escuela y hora en Argentina (UTC-3)
- **PDF Historial de Carros** — landscape, 9 columnas incluyendo Autorizó Retiro y Autorizó Devolución
- **PDF Historial Espacio Digital** — landscape, 9 columnas incluyendo Carro(s) y Autorizó Retiro/Devolución
- **PDF Historial Televisores** — landscape, 9 columnas
- **PDF Parte de Alerta** — generado cuando el préstamo supera 2 horas. Datos del docente, préstamo y netbooks del carro. Tres líneas de firma.
- **PDF Control Masivo de Stock** — landscape, 3 secciones: encontradas, no en sistema, ausentes del listado
- **PDF Horario de Docente** — landscape A4, grilla completa con carro asignado por módulo
- **PDF Servicio Técnico** — carros físicos en servicio + netbooks en servicio
- **PDF Estadísticas** — top docentes y top materias discriminadas por módulo horario

### Estadísticas
Accesible desde el sidebar bajo **Reportes → Estadísticas**. Solo visible para Directivo y Administrador.

- **Tarjetas resumen:** total histórico de préstamos de carros, préstamos del mes actual, carro más prestado y docente más activo
- **Tabla ranking de carros:** ordenada por cantidad de préstamos históricos, con barra visual proporcional, total del mes y fecha del último préstamo
- **Top Docentes:** ranking de los 10 docentes con más préstamos históricos
- **Top Materias:** ranking de materias más solicitadas, discriminadas por módulo horario. Cada préstamo registra la materia específica que el docente daba en ese módulo al momento del retiro — los docentes con varias materias aparecen desglosados

### ♻️ Obsolescencia y Reemplazos
Accesible desde **Inventario → Obsolescencia**. Visible para **todos los roles**.

Registra netbooks que quedan fuera de servicio de forma definitiva (irreparables, vandalizadas, robadas, etc.) y permite rastrear si fueron reemplazadas por equipos nuevos.

**Flujo completo:**
1. Se registra la netbook obsoleta con motivo (irreparable, rotura total, vandalismo, etc.) — la netbook queda marcada como `de_baja` automáticamente
2. Cuando llega el equipo nuevo, se registra el reemplazo con número de serie y modelo
3. Al registrar el reemplazo, dos opciones:
   - **Asignar a un carro ahora** → la netbook nueva entra directamente al carro seleccionado
   - **Dejar pendiente** → aparece en **Novedades del día** como alerta hasta que se asigne

| Campo registrado | Descripción |
|-----------------|-------------|
| Netbook obsoleta | N° interno, serie, carro de origen |
| Motivo de baja | Irreparable, rotura, vandalismo, robada, intercambiada por BA Colaborativa, etc. |
| Observaciones | Descripción libre del estado |
| Reemplazo — serie | N° de serie del equipo nuevo |
| Reemplazo — modelo | Modelo del equipo nuevo |
| Reemplazo — carro destino | Carro al que se asigna la nueva netbook |
| Estado | Sin reemplazo / Pendiente de asignación / Reemplazada ✅ |

**Filtros disponibles:** Todas · ⏳ Pendientes · ✅ Con reemplazo · ❌ Sin reemplazo

### Importar Horarios de Docentes
Accesible desde **Sistema → Horarios Docentes**. Excel directo (`.xlsx`) o Google Sheets.

- Los módulos se **acumulan** — no se borran al importar una segunda planilla
- Para docentes con turno **Mañana y Tarde**: subir las dos planillas en cualquier orden, los módulos de cada turno se suman sin pisarse
- El nombre del archivo debe tener el formato `APELLIDO_NOMBRE_HORARIO_2026.xlsx`
- Para docentes con apellido compuesto o que el sistema no encuentre automáticamente, el formulario tiene un selector para elegirlos manualmente

### Sistema
- **Config. Espacio Digital** — Accesible para todos los roles. Hasta 2 carros.
- **Config. Sistema** — Solo Directivo y Administrador. Permite editar materias/cargos, horarios de módulos y templates de mails. Los templates cubren retiro/devolución de **carros, netbooks (Espacio Digital) y televisores**. Los cambios se reflejan en tiempo real en toda la app.
- **Importar Drive** — Solo Directivo y Administrador
- **Notificaciones** — Solo Directivo y Administrador
- **Backups** — Solo Directivo y Administrador
- **Sesiones** — Solo Directivo y Administrador. Historial de sesiones de Encargados con IP, dispositivo, duración en vivo y cierre forzado.

---

## 🎟️ Tickets BA Colaborativa

Accesible desde **Inventario → Tickets BA**.

Los tickets registran reclamos a BA Colaborativa vinculados a netbooks o carros en servicio técnico. En lugar de eliminarlos cuando se resuelven, el sistema los **archiva** para conservar el historial.

| Acción | Descripción |
|--------|-------------|
| **Nuevo Ticket** | Abre modal con N° de reclamo, observaciones y selección de equipos |
| **Resuelto** (botón verde) | Archiva el ticket con fecha, motivo y quién cerró — no elimina |
| **Reabrir** (ícono undo) | Reactiva un ticket resuelto si el problema reaparece |
| **Eliminar** (ícono tacho) | Eliminación definitiva — solo disponible desde la sección de resueltos |

La sección **Tickets Resueltos** aparece colapsada debajo de los activos. Muestra fecha de cierre, motivo y responsable del cierre.

---

## 💻 Asignaciones Internas

Accesible desde **Inventario → Asignaciones Internas**. Solo visible para Directivo y Administrador.

Registra netbooks entregadas de forma permanente a un docente o área que no están en ningún carro.

| Campo | Descripción |
|-------|-------------|
| N° Interno | Número interno del equipo (libre) |
| N° Serie | Número de serie del equipo (libre) |
| Modelo | Descripción del modelo |
| Destinatario | Docente del sistema (selector) o área libre |
| Motivo | Descripción de por qué se asigna el equipo |

Las asignaciones activas se suman a **Netbooks operativas** y al **Total de netbooks** en el dashboard. Los equipos participan en el cruce del Control Masivo de Stock.

---

## 📺 Televisores

Accesible desde **Inventario → Televisores** y desde **Préstamos → Televisores** (atajo directo a préstamos activos).

Las TVs del establecimiento están ubicadas habitualmente en el **Aula Magna** y se trasladan a otras aulas cuando un docente las solicita. El préstamo registra quién la llevó y adónde.

### Componentes registrados por TV
Control remoto · Cable HDMI · Cable VGA · Cable de corriente · Soporte de pared · Soporte de pie · Chromecast · Adaptador HDMI/USB-C · Campo libre

### Estados
| Estado | Descripción |
|--------|-------------|
| `disponible` | Lista para préstamo |
| `prestada` | Fuera del repositorio |
| `en_servicio` | En servicio técnico — bloqueada para préstamos |
| `de_baja` | Dada de baja definitiva |

---

## 🔧 Servicio técnico de carro físico

1. En **Inventario → Carros**, clic en 🔧
2. Seleccionar motivo y confirmar
3. El carro queda bloqueado para préstamos
4. El sistema redirige a **Transferir Netbooks** con el carro origen preseleccionado

Motivos: Térmica quemada · Cerradura rota · Rueda rota · Estructura/chasis dañado · Problema eléctrico · Otro

---

## 📦 Control Masivo de Stock

Desde **Inventario → Stock Masivo**. Cruza un listado externo de números de serie contra todas las netbooks del sistema (carros + asignaciones internas).

| Método | Descripción |
|--------|-------------|
| **Excel** | `.xlsx` — lee todas las celdas de la primera hoja |
| **Google Sheets** | URL + nombre de pestaña |
| **Manual** | Pegá los números de serie uno por línea |

| Sección | Descripción |
|---------|-------------|
| ✅ Encontradas | En el listado Y en el sistema |
| ❌ No encontradas | En el listado pero NO en el sistema |
| ⚠️ No en listado | En el sistema pero NO en el listado — posibles faltantes |

---

## 🖨️ Parte de Alerta — Préstamo en Demora

Cuando un préstamo de carro supera las **2 horas**, aparece el botón **🖨 Parte** que genera el PDF con datos del docente, préstamo, netbooks del carro y tres líneas de firma.

---

## 🔒 Sesiones de Encargados

Desde **Sistema → Sesiones**. Registro automático de IP, user agent y hora. Duración en vivo cada 30 segundos. Cierre forzado individual o masivo con auditoría.

---

## ⏰ Horarios de módulos

| Código | Horario | Turno |
|--------|---------|-------|
| M1 | 07:30 - 08:10 | Mañana |
| M2 | 08:10 - 08:50 | Mañana |
| M3 | 09:00 - 09:40 | Mañana |
| M4 | 09:40 - 10:20 | Mañana |
| M5 | 10:30 - 11:10 | Mañana |
| M6 | 11:10 - 11:50 | Mañana |
| M7 | 12:00 - 12:40 | Mañana |
| M8/T1 | 12:40 - 13:20 | Compartido |
| T2 | 13:20 - 14:00 | Tarde |
| T3 | 14:00 - 14:40 | Tarde |
| T4 | 14:50 - 15:30 | Tarde |
| T5 | 15:30 - 16:10 | Tarde |
| T6 | 16:20 - 17:00 | Tarde |
| T7 | 17:00 - 17:40 | Tarde |
| T8 | 17:40 - 18:20 | Tarde |

---

## 👤 Gestión de usuarios

- **Admin y Directivo** pueden editar el username y el correo de cualquier usuario
- Cada usuario puede editar su propio nombre, apellido y username desde Mi Perfil

---

## 🎓 Asignación de alumnos a netbooks

- Cada carro tiene entre 30 y 32 netbooks
- Se asigna un grupo de mañana y un grupo de tarde al mismo carro
- Asignación automática desde **Carros → [carro] → Asignación automática**

---

## 👨‍🏫 Baja de docentes

| Motivo | Efecto |
|--------|--------|
| **Jubilación** | Elimina el registro permanentemente. No aparece en inactivos. |
| Renuncia / Traslado / Otro | Marca el docente como inactivo. Puede reactivarse. |

---

## 📧 Sistema de notificaciones por mail

| Evento | Destinatario |
|--------|-------------|
| Retiro de carro | Docente |
| Devolución de carro | Docente |
| Retiro de netbooks | Docente |
| Devolución de netbooks | Docente |
| Alerta de demora | ConfigNotificacion |
| Alerta fin de módulo | ConfigNotificacion |

---

## 🛠️ Solución de problemas frecuentes

### Error 404 al intentar devolución individual de netbook
Verificar que `routes/prestamos.py` tenga el endpoint `devolucion_netbook_individual` registrado antes de `devolucion_netbooks`.

### El carro en servicio técnico no aparece bloqueado en el formulario de retiro
Verificar que `retiro_carro()` incluya `carros_servicio_ids` en `prestamos_activos_ids`.

### Deploy falla con ImportError de ubicaciones_bp
El módulo Ubicaciones fue descartado. Verificar que `app.py` no importe ni registre `ubicaciones_bp`.

### PDF historial de TVs desbordado
Verificar que los anchos de columna en `pdf_historial_tvs()` sumen ≤ 247mm (ancho útil A4 landscape con márgenes 1.5cm).

### Error al ejecutar migrate_tvs.py — tabla ya existe
Si el error es `already exists`, la migración ya fue ejecutada — es seguro ignorarlo.

### Error al ejecutar migrate_asignaciones_internas.py — `conn.commit()` no disponible
El objeto `Connection` de SQLAlchemy 1.4 no tiene `.commit()`. La migración usa `psycopg2` directamente con `conn.autocommit = True`.

### Error 500 en dashboard — columna `fecha_servicio` no existe en netbooks
Ejecutar desde la Shell de Render:
```bash
python - << 'EOF'
import os, psycopg2
conn = psycopg2.connect(os.environ['DATABASE_URL'])
conn.autocommit = True
cur = conn.cursor()
cur.execute("ALTER TABLE netbooks ADD COLUMN IF NOT EXISTS fecha_servicio TIMESTAMP;")
print("OK")
cur.close(); conn.close()
EOF
```

### El PDF del control masivo dice "no hice la búsqueda"
La session de Flask tiene un límite de ~4 KB. Verificar que `routes/stock.py` guarde solo `session['stock_masivo_series']` (lista de strings) y no el resultado completo.

### En Tickets BA no aparecen los carros en servicio
Verificar que la tabla `tickets_ba_netbooks` tenga la columna `carro_id`. Si no existe, ejecutar `python migrate_ticket_ba_carro.py`.

### Los PDFs muestran hora incorrecta
Verificar que `ARG_OFFSET = timedelta(hours=-3)` en `app.py` y `pdf_reportes.py`.

### Las netbooks se muestran desordenadas dentro del carro
El campo `numero_interno` es texto en la BD. El ordenamiento se aplica en Python con `int()`. Verificar que `carros.py` tenga el `.sort(key=lambda nb: int(nb.numero_interno) if nb.numero_interno and nb.numero_interno.isdigit() else 9999)` antes del `render_template`.

### Se puede registrar dos netbooks con el mismo número interno en el mismo carro
Verificar que `routes/netbooks.py` tenga la validación `Netbook.query.filter_by(carro_id=..., numero_interno=...)` en `nuevo()` y `editar()`, y que el endpoint `GET /netbooks/verificar-numero-interno` esté registrado.

### Error 500 en /estadisticas — invalid input syntax for type integer
PostgreSQL no puede hacer `CAST(numero_fisico AS INTEGER)` cuando algún carro tiene nombre de texto (ej: "CARRO AZUL"). Verificar que `routes/main.py` ordene los carros en Python con `carros.sort(key=lambda c: int(c.numero_fisico) if c.numero_fisico and c.numero_fisico.isdigit() else 9999)` y no use `order_by` con cast en la query.

### Módulos de horario no se importan correctamente desde Excel
La planilla usa formato `8.10 a 8.50` (punto decimal, minúscula). La función `_normalizar_horario()` en `importar_drive.py` convierte cualquier variante al formato con ceros `08.10 a 08.50` que matchea el diccionario `_HORARIO_A_MODULO`. Si los módulos quedan vacíos, verificar que la versión actualizada del 28/04/2026 esté deployada.

### Docente con turno Mañana y Tarde pierde módulos al importar la segunda planilla
El import usa `acumular=True` por defecto desde el 28/04/2026 — los módulos existentes nunca se borran. Verificar que `importar_drive.py` tenga la lógica de acumulación con `HorarioDocente.query.filter_by(...)` antes de agregar cada módulo.

### En estadísticas todos los préstamos aparecen como "Sin materia asignada"
Los préstamos anteriores al 28/04/2026 no tienen `materia_prestamo`. Es normal. Los nuevos préstamos se registran con la materia del módulo actual al momento del retiro. Verificar que `migrate_materia_prestamo.py` haya sido ejecutado en la Shell de Render.

### Error 500 al abrir /mensajeria/ — Table 'mensajes' is already defined
`routes/mensajeria.py` definía `Mensaje` y `MensajeLeid` de forma dinámica dentro de `_get_models()`. Como `models/__init__.py` ya los registraba en el mismo MetaData, al llamar `_get_models()` SQLAlchemy lanzaba `InvalidRequestError`. Verificar que `routes/mensajeria.py` use `from models import db, Mensaje, MensajeLeid` al inicio y no defina esas clases inline.

### La tabla mensajes no existe — Error al abrir mensajería
Ejecutar desde la Shell de Render:
```bash
python migrate_mensajeria.py
```

### Los cargos agregados en Config. Sistema no aparecen en el selector de materia del formulario de docentes
`routes/docentes.py` importaba la lista `MATERIAS` hardcodeada al arrancar el servidor — ese valor nunca se actualiza. Verificar que el archivo use `from models_extra.horarios_notificaciones import _get_materias_activas` y que `nuevo()` y `editar()` pasen `materias=_get_materias_activas()` al template en lugar de `materias=MATERIAS`.

### El buscador de docente no aparece en el préstamo de TV — sigue mostrando un select
El template `templates/tvs/prestar.html` es la versión anterior. Reemplazarlo por la versión actualizada del 29/04/2026 que usa el buscador con autocomplete idéntico al de retiro de carro. No requiere cambios en `routes/tvs.py` ni migraciones.

### Error 500 en /tickets-ba/ — column tickets_ba.estado does not exist
El código fue actualizado antes de ejecutar la migración. Ejecutar desde la Shell de Render:
```bash
python migrate_ticket_ba_estado.py
```

### Los tickets resueltos no aparecen — la sección de resueltos está vacía
Es el comportamiento esperado si aún no se cerró ningún ticket. Los tickets existentes quedan como `activo` después de la migración. Cerrar uno con el botón verde **Resuelto** para que aparezca en la sección colapsable.

### Error 500 en /obsolescencia/ — column n.modelo does not exist
La tabla `netbooks` no tiene columna `modelo`. Verificar que `routes/obsolescencia.py` sea la versión del 30/04/2026 que no referencia `n.modelo` en ninguna query. Si el error persiste, ejecutar el push con la versión corregida.

---

## 💾 Backups

- **Local:** Automáticos cada 24 horas en carpeta `backups/`
- **Producción:** Usar el sistema de backup de Render para PostgreSQL

---

## 📄 Documentación

| Documento | Descripción |
|-----------|-------------|
| `Manual_SIGA-Tec.pdf` | Manual de usuario completo. 13 secciones con identidad visual institucional. |
| `LISTADOS_SIGATEC_2026.xlsx` | Listados de alumnos 2026. 28 pestañas con formato `NxGy TM/TT`. |
| `BITACORA_SIGATEC.md` | Bitácora técnica del proyecto. |

---

## 🚀 Deploy en producción (Render)

**URL de producción:** https://sigatec-et7.onrender.com

### Variables de entorno en Render

| Variable | Descripción |
|----------|-------------|
| `SECRET_KEY` | Generada automáticamente por Render |
| `DATABASE_URL` | Conexión a PostgreSQL |
| `GOOGLE_CLIENT_ID` | ID de cliente OAuth web |
| `GOOGLE_CLIENT_SECRET` | Secreto del cliente OAuth web |
| `FLASK_ENV` | `production` |
| `GMAIL_USER` | `aulamagnaespaciodigital@gmail.com` |
| `GMAIL_APP_PASSWORD` | App Password de 16 caracteres |

### Redirect URI en Google Cloud Console

```
https://sigatec-et7.onrender.com/google_auth/google/authorized
```

> ⚠️ El servicio se "duerme" después de 15 minutos sin uso en el plan gratuito. La primera visita puede tardar 30-60 segundos.

---

### SyntaxError al deployar — f-string expression part cannot include a backslash
Python 3.11 no permite `\"` dentro de expresiones en f-strings. Verificar que `services/mail.py` use `pulgadas_str = f' ({tv.pulgadas}")'` como variable previa en las funciones de mail de TV.

### Error 500 al abrir Config. Sistema — column mail_retiro_tv does not exist
Las columnas nuevas no existen hasta ejecutar la migración. Ejecutar desde la Shell de Render:
```bash
python migrate_mail_tv.py
```

### Las TVs no aparecen en Administrar Historial — sección 3
Verificar que `routes/mantenimiento.py` sea la versión del 01/05/2026 que importa `PrestamoTV` y que `prestamos_docente()` incluye el bloque de TVs. Verificar que `limpiar_pruebas.html` tenga la tabla `s3-tbody-tvs` y el bloque `// ── TVs ──` en `cargarPrestamos()`.

### El mail de TV no usa el template de Config. Sistema
Verificar que `services/mail.py` sea la versión del 01/05/2026 que llama `_get_template_mail('mail_retiro_tv')` y `_get_template_mail('mail_devolucion_tv')` antes de usar el cuerpo por defecto.

---

## 📞 Contacto y soporte

**Desarrollado para:** E.T. N°7 D.E. 5 — Dolores Lavalle de Lavalle
**Administrador del sistema:** N. Montefinal Turnes
**Correo:** nicolas.montefinal@bue.edu.ar
