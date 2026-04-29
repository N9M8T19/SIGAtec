from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from models import db, Carro, Netbook, Docente, PrestamoCarro, PrestamoNetbook, PrestamoNetbookItem, TicketBA, Usuario, ConfigEspacioDigital, Alumno, AsignacionInterna, TV, PrestamoTV
from datetime import datetime

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
@main_bp.route('/dashboard')
@login_required
def dashboard():
    total_carros   = Carro.query.filter(Carro.estado != 'baja').count()
    total_netbooks = Netbook.query.count()
    operativas     = Netbook.query.filter_by(estado='operativa').count()
    en_servicio    = Netbook.query.filter_by(estado='servicio_tecnico').count()
    total_docentes = Docente.query.filter_by(activo=True).count()
    prestamos_activos = PrestamoCarro.query.filter_by(estado='activo').count()
    nb_prestadas = PrestamoNetbook.query.filter_by(estado='activo').count()
    tvs_prestadas = PrestamoTV.query.filter_by(estado='activo').count()

    # Asignaciones internas — se suman a operativas y al total de netbooks
    asignaciones_activas = AsignacionInterna.query.filter_by(activa=True).count()
    total_netbooks += asignaciones_activas
    operativas     += asignaciones_activas

    from config import Config
    limite  = Config.MINUTOS_ALERTA_PRESTAMO
    ahora   = datetime.utcnow()
    alertas = []

    for p in PrestamoCarro.query.filter_by(estado='activo').all():
        mins = int((ahora - p.hora_retiro).total_seconds() / 60)
        if mins >= limite:
            alertas.append({
                'tipo':    'Carro',
                'docente': p.docente.nombre_completo,
                'item':    p.carro.display,
                'tiempo':  p.tiempo_transcurrido
            })

    for p in PrestamoNetbook.query.filter_by(estado='activo').all():
        mins = int((ahora - p.hora_retiro).total_seconds() / 60)
        if mins >= limite:
            alertas.append({
                'tipo':    'Netbooks',
                'docente': p.docente.nombre_completo,
                'item':    f"{len(p.items)} netbook(s)",
                'tiempo':  p.tiempo_transcurrido
            })

    stats = {
        'total_carros':        total_carros,
        'total_netbooks':      total_netbooks,
        'operativas':          operativas,
        'en_servicio':         en_servicio,
        'total_docentes':      total_docentes,
        'prestamos_activos':   prestamos_activos,
        'nb_prestadas':        nb_prestadas,
        'asignaciones_activas': asignaciones_activas,
        'tvs_prestadas':       tvs_prestadas,
    }

    return render_template('main/dashboard.html',
                           stats=stats, alertas=alertas, now=ahora)


# ─────────────────────────────────────────────────────────────────────────────
#  ESTADÍSTICAS — solo Directivo y Administrador
#  ⚠️ Nuevo 28/04/2026 — préstamos por carro (histórico + mes actual)
# ─────────────────────────────────────────────────────────────────────────────

@main_bp.route('/estadisticas')
@login_required
def estadisticas():
    if not current_user.tiene_permiso('estadisticas'):
        flash('No tenés permisos para acceder a esta sección.', 'danger')
        return redirect(url_for('main.dashboard'))

    from sqlalchemy import func
    from datetime import date, timedelta
    from zoneinfo import ZoneInfo
    from datetime import timezone

    AR = ZoneInfo('America/Argentina/Buenos_Aires')
    ahora_ar = datetime.utcnow().replace(tzinfo=timezone.utc).astimezone(AR)

    # ── Mes actual ──────────────────────────────────────────────────────────
    inicio_mes_ar = ahora_ar.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    inicio_mes_utc = inicio_mes_ar.astimezone(timezone.utc).replace(tzinfo=None)

    # ── Préstamos de carros agrupados por carro — histórico total ───────────
    filas_historico = (
        db.session.query(
            PrestamoCarro.carro_id,
            func.count(PrestamoCarro.id).label('total')
        )
        .group_by(PrestamoCarro.carro_id)
        .all()
    )
    hist_por_carro = {fila.carro_id: fila.total for fila in filas_historico}

    # ── Préstamos de carros agrupados por carro — mes actual ────────────────
    filas_mes = (
        db.session.query(
            PrestamoCarro.carro_id,
            func.count(PrestamoCarro.id).label('total')
        )
        .filter(PrestamoCarro.hora_retiro >= inicio_mes_utc)
        .group_by(PrestamoCarro.carro_id)
        .all()
    )
    mes_por_carro = {fila.carro_id: fila.total for fila in filas_mes}

    # ── Último préstamo por carro ────────────────────────────────────────────
    filas_ultimo = (
        db.session.query(
            PrestamoCarro.carro_id,
            func.max(PrestamoCarro.hora_retiro).label('ultimo')
        )
        .group_by(PrestamoCarro.carro_id)
        .all()
    )
    ultimo_por_carro = {fila.carro_id: fila.ultimo for fila in filas_ultimo}

    # ── Armar tabla por carro ────────────────────────────────────────────────
    carros = Carro.query.filter(Carro.estado != 'baja').all()
    carros.sort(key=lambda c: int(c.numero_fisico) if c.numero_fisico and c.numero_fisico.isdigit() else 9999)

    def hora_arg(dt):
        if dt is None:
            return '—'
        dt_utc = dt.replace(tzinfo=timezone.utc)
        return dt_utc.astimezone(AR).strftime('%d/%m/%Y %H:%M hs')

    stats_carros = []
    for c in carros:
        total_hist = hist_por_carro.get(c.id, 0)
        total_mes  = mes_por_carro.get(c.id, 0)
        ultimo     = ultimo_por_carro.get(c.id)
        stats_carros.append({
            'carro':      c,
            'total':      total_hist,
            'mes':        total_mes,
            'ultimo':     hora_arg(ultimo),
        })

    # Ordenar de mayor a menor préstamos históricos para el ranking
    stats_carros_ranking = sorted(stats_carros, key=lambda x: x['total'], reverse=True)

    # ── Totales generales ────────────────────────────────────────────────────
    total_prestamos_hist = sum(r['total'] for r in stats_carros)
    total_prestamos_mes  = sum(r['mes']   for r in stats_carros)

    # ── Docente más activo (más préstamos históricos de carros) ─────────────
    fila_docente = (
        db.session.query(
            PrestamoCarro.docente_id,
            func.count(PrestamoCarro.id).label('total')
        )
        .group_by(PrestamoCarro.docente_id)
        .order_by(func.count(PrestamoCarro.id).desc())
        .first()
    )
    docente_top = None
    docente_top_total = 0
    if fila_docente:
        docente_top = Docente.query.get(fila_docente.docente_id)
        docente_top_total = fila_docente.total

    # ── Carro más prestado ──────────────────────────────────────────────────
    carro_top = stats_carros_ranking[0] if stats_carros_ranking else None

    # ── Nombre del mes actual ────────────────────────────────────────────────
    MESES = ['Enero','Febrero','Marzo','Abril','Mayo','Junio',
             'Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']
    nombre_mes = f"{MESES[ahora_ar.month - 1]} {ahora_ar.year}"

    # ── Top docentes por préstamos históricos ───────────────────────────────
    filas_top_docentes = (
        db.session.query(
            PrestamoCarro.docente_id,
            func.count(PrestamoCarro.id).label('total')
        )
        .group_by(PrestamoCarro.docente_id)
        .order_by(func.count(PrestamoCarro.id).desc())
        .limit(10)
        .all()
    )
    top_docentes = []
    for fila in filas_top_docentes:
        doc = Docente.query.get(fila.docente_id)
        if doc:
            top_docentes.append((doc, fila.total))

    # ── Top materias por préstamos — usa materia_prestamo si existe ──────────
    # Cada préstamo tiene materia_prestamo (materia específica del módulo).
    # Si es None (préstamos viejos sin ese campo), cae en 'Sin materia'.
    filas_top_materias = (
        db.session.query(
            PrestamoCarro.materia_prestamo,
            func.count(PrestamoCarro.id).label('total')
        )
        .group_by(PrestamoCarro.materia_prestamo)
        .order_by(func.count(PrestamoCarro.id).desc())
        .limit(10)
        .all()
    )
    top_materias = [(fila.materia_prestamo, fila.total) for fila in filas_top_materias]

    return render_template(
        'main/estadisticas.html',
        stats_carros=stats_carros,
        stats_carros_ranking=stats_carros_ranking,
        total_prestamos_hist=total_prestamos_hist,
        total_prestamos_mes=total_prestamos_mes,
        docente_top=docente_top,
        docente_top_total=docente_top_total,
        carro_top=carro_top,
        nombre_mes=nombre_mes,
        top_docentes=top_docentes,
        top_materias=top_materias,
    )


@main_bp.route('/api/novedades')
@login_required
def novedades():
    """Devuelve los últimos eventos del sistema para el panel de novedades del dashboard."""
    from zoneinfo import ZoneInfo

    AR = ZoneInfo('America/Argentina/Buenos_Aires')
    from datetime import timezone
    ahora = datetime.utcnow()
    ahora_ar = ahora.replace(tzinfo=timezone.utc).astimezone(AR)
    inicio_dia_ar = ahora_ar.replace(hour=0, minute=0, second=0, microsecond=0)
    hoy_utc = inicio_dia_ar.astimezone(timezone.utc).replace(tzinfo=None)

    def hora_ar(dt):
        if dt is None:
            return '—'
        dt_utc = dt.replace(tzinfo=timezone.utc)
        dt_local = dt_utc.astimezone(AR)
        return dt_local.strftime('%d/%m %H:%M hs')

    eventos = []

    # Retiros y devoluciones de carros (últimos 5)
    prestamos_carros = PrestamoCarro.query.filter(
        PrestamoCarro.hora_retiro >= hoy_utc
    ).order_by(PrestamoCarro.hora_retiro.desc()).limit(10).all()

    for p in prestamos_carros:
        docente = p.docente.nombre_completo if p.docente else '—'
        carro = p.carro.display if p.carro else '—'
        if p.estado == 'devuelto' and p.hora_devolucion:
            eventos.append({
                'tipo': 'devolucion',
                'label': 'Devolución',
                'texto': f'{docente} devolvió {carro}',
                'hora': hora_ar(p.hora_devolucion),
                '_dt': p.hora_devolucion
            })
        else:
            eventos.append({
                'tipo': 'retiro',
                'label': 'Retiro',
                'texto': f'{docente} retiró {carro}',
                'hora': hora_ar(p.hora_retiro),
                '_dt': p.hora_retiro
            })

    # Retiros y devoluciones de netbooks (últimos 5)
    prestamos_nb = PrestamoNetbook.query.filter(
        PrestamoNetbook.hora_retiro >= hoy_utc
    ).order_by(PrestamoNetbook.hora_retiro.desc()).limit(10).all()

    for p in prestamos_nb:
        docente = p.docente.nombre_completo if p.docente else '—'
        cant = len(p.items)
        if p.estado == 'devuelto' and p.hora_devolucion:
            eventos.append({
                'tipo': 'devolucion',
                'label': 'Devolución',
                'texto': f'{docente} devolvió {cant} netbook(s) — Espacio Digital',
                'hora': hora_ar(p.hora_devolucion),
                '_dt': p.hora_devolucion
            })
        else:
            eventos.append({
                'tipo': 'retiro',
                'label': 'Retiro',
                'texto': f'{docente} retiró {cant} netbook(s) — Espacio Digital',
                'hora': hora_ar(p.hora_retiro),
                '_dt': p.hora_retiro
            })

    # Tickets BA (últimos 5)
    try:
        tickets = TicketBA.query.filter(
            TicketBA.fecha_creacion >= hoy_utc
        ).order_by(TicketBA.id.desc()).limit(5).all() if hasattr(TicketBA, 'fecha_creacion') else []
        for t in tickets:
            eventos.append({
                'tipo': 'ticket',
                'label': 'Ticket BA',
                'texto': f'Ticket #{t.id} — {t.descripcion[:60] if t.descripcion else "sin descripción"}',
                'hora': hora_ar(t.fecha_creacion) if hasattr(t, 'fecha_creacion') else '—',
                '_dt': t.fecha_creacion if hasattr(t, 'fecha_creacion') else None
            })
    except Exception:
        pass

    # Netbooks enviadas a servicio técnico hoy
    try:
        netbooks_hoy = Netbook.query.filter(
            Netbook.estado == 'servicio_tecnico',
            Netbook.fecha_servicio != None,
            Netbook.fecha_servicio >= hoy_utc
        ).order_by(Netbook.fecha_servicio.desc()).limit(10).all()
        for nb in netbooks_hoy:
            carro_txt = f'Carro {nb.carro.numero_fisico}' if nb.carro and nb.carro.numero_fisico else 'sin carro'
            eventos.append({
                'tipo':  'servicio',
                'label': 'Serv. Técnico',
                'texto': f'Netbook N°{nb.numero_interno or "—"} ({carro_txt}) enviada a servicio',
                'hora':  hora_ar(nb.fecha_servicio),
                '_dt':   nb.fecha_servicio
            })
    except Exception:
        pass

    # Carros físicos enviados a servicio técnico hoy
    try:
        carros_hoy = Carro.query.filter(
            Carro.estado == 'en_servicio',
            Carro.fecha_servicio != None,
            Carro.fecha_servicio >= hoy_utc
        ).order_by(Carro.fecha_servicio.desc()).limit(5).all()
        for c in carros_hoy:
            motivo_txt = c.motivo_servicio or 'sin motivo'
            eventos.append({
                'tipo':  'servicio',
                'label': 'Serv. Técnico',
                'texto': f'Carro {c.display} enviado a servicio — {motivo_txt}',
                'hora':  hora_ar(c.fecha_servicio),
                '_dt':   c.fecha_servicio
            })
    except Exception:
        pass

    # Préstamos de TVs hoy
    try:
        from models import PrestamoTV
        prestamos_tv = PrestamoTV.query.filter(
            PrestamoTV.fecha_retiro >= hoy_utc
        ).order_by(PrestamoTV.fecha_retiro.desc()).limit(10).all()
        for p in prestamos_tv:
            docente = p.docente.nombre_completo if p.docente else (p.nombre_solicitante or '—')
            tv_cod  = p.tv.codigo if p.tv else '—'
            if p.estado == 'devuelto' and p.fecha_devolucion_real:
                eventos.append({
                    'tipo':  'devolucion',
                    'label': 'TV Devuelta',
                    'texto': f'{docente} devolvió {tv_cod}',
                    'hora':  hora_ar(p.fecha_devolucion_real),
                    '_dt':   p.fecha_devolucion_real
                })
            else:
                eventos.append({
                    'tipo':  'retiro',
                    'label': 'TV Prestada',
                    'texto': f'{docente} retiró {tv_cod}',
                    'hora':  hora_ar(p.fecha_retiro),
                    '_dt':   p.fecha_retiro
                })
    except Exception:
        pass

    # Ordenar por fecha descendente, los que no tienen fecha van al final
    eventos.sort(key=lambda e: e['_dt'] or datetime.min, reverse=True)

    # Limpiar campo interno antes de devolver
    for e in eventos:
        del e['_dt']

    return jsonify({'novedades': eventos[:10]})


# ─────────────────────────────────────────────────────────────────────────────
#  BÚSQUEDA GLOBAL — carros, netbooks, alumnos
# ─────────────────────────────────────────────────────────────────────────────

@main_bp.route('/api/buscar')
@login_required
def buscar():
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify({'carros': [], 'netbooks': [], 'alumnos': []})

    carros = Carro.query.filter(
        Carro.estado != 'baja',
        db.or_(
            Carro.numero_serie.ilike(f'%{q}%'),
            Carro.numero_fisico.ilike(f'%{q}%'),
            Carro.aula.ilike(f'%{q}%'),
            Carro.division.ilike(f'%{q}%'),
        )
    ).limit(5).all()

    netbooks = Netbook.query.filter(
        db.or_(
            Netbook.numero_serie.ilike(f'%{q}%'),
            Netbook.numero_interno.ilike(f'%{q}%'),
            Netbook.alumno.ilike(f'%{q}%'),
        )
    ).limit(5).all()

    alumnos = Alumno.query.filter(
        db.or_(
            Alumno.nombre.ilike(f'%{q}%'),
            Alumno.apellido.ilike(f'%{q}%'),
            Alumno.curso.ilike(f'%{q}%'),
            Alumno.dni.ilike(f'%{q}%'),
        )
    ).limit(5).all()

    def alumno_nb(n):
        if n.alumno_manana:
            return f'{n.alumno_manana.apellido}, {n.alumno_manana.nombre}'
        if n.alumno_tarde:
            return f'{n.alumno_tarde.apellido}, {n.alumno_tarde.nombre}'
        return n.alumno or 'Sin asignar'

    def carro_display(c):
        partes = []
        if c.numero_fisico:
            partes.append(f'Carro {c.numero_fisico}')
        if c.division:
            partes.append(c.division)
        return ' — '.join(partes) if partes else f'ID {c.id}'

    return jsonify({
        'carros': [{
            'id':      c.id,
            'nombre':  carro_display(c),
            'serie':   c.numero_serie or '—',
            'netbooks': len(c.netbooks),
            'estado':  c.estado,
            'url':     url_for('carros.netbooks', id=c.id),
        } for c in carros],
        'netbooks': [{
            'id':      n.id,
            'serie':   n.numero_serie or '—',
            'interno': n.numero_interno or '—',
            'alumno':  alumno_nb(n),
            'carro':   f'Carro {n.carro.numero_fisico}' if n.carro and n.carro.numero_fisico else '—',
            'estado':  n.estado,
            'url':     url_for('carros.netbooks', id=n.carro_id),
        } for n in netbooks],
        'alumnos': [{
            'id':      a.id,
            'nombre':  f'{a.apellido}, {a.nombre}',
            'curso':   a.curso or '—',
            'turno':   'Mañana' if a.turno == 'M' else 'Tarde',
            'netbook': a.netbook_asignada.numero_serie if a.netbook_asignada else 'Sin netbook',
            'url':     url_for('carros.index'),
        } for a in alumnos],
    })


# ─────────────────────────────────────────────────────────────────────────────
#  CONFIGURACIÓN ESPACIO DIGITAL — asignar carro
# ─────────────────────────────────────────────────────────────────────────────

@main_bp.route('/configuracion/espacio-digital', methods=['GET', 'POST'])
@login_required
def config_espacio_digital():
    if not (current_user.tiene_permiso('configuracion') or current_user.rol == 'Encargado'):
        flash('Credenciales no válidas.', 'danger')
        return redirect(url_for('main.dashboard'))

    config = ConfigEspacioDigital.query.first()
    carros = Carro.query.filter(Carro.estado != 'baja').order_by(Carro.numero_fisico).all()

    if request.method == 'POST':
        carro_id       = request.form.get('carro_id', type=int)
        carro_id_2     = request.form.get('carro_id_2', type=int) or None
        nombre         = request.form.get('nombre', 'Carro Espacio Digital').strip()
        minutos_alerta = request.form.get('minutos_alerta', 120, type=int)

        if carro_id_2 and carro_id_2 == carro_id:
            flash('El Carro 2 debe ser diferente al Carro 1.', 'danger')
            return redirect(url_for('main.config_espacio_digital'))

        if not config:
            config = ConfigEspacioDigital()
            db.session.add(config)

        config.carro_id       = carro_id
        config.carro_id_2     = carro_id_2
        config.nombre         = nombre
        config.minutos_alerta = minutos_alerta
        db.session.commit()
        flash('Configuración del Espacio Digital actualizada.', 'success')
        return redirect(url_for('prestamos.espacio_digital'))

    return render_template('main/config_espacio_digital.html',
                           config=config, carros=carros)


# ─────────────────────────────────────────────────────────────────────────────
#  CONFIGURACIÓN DEL SISTEMA — solo Directivo y Administrador
#  ⚠️ Nuevo — gestión de materias, cargos, módulos horarios y templates de mail
# ─────────────────────────────────────────────────────────────────────────────

@main_bp.route('/configuracion/sistema', methods=['GET', 'POST'])
@login_required
def config_sistema():
    if not current_user.tiene_permiso('configuracion'):
        flash('No tenés permisos para acceder a esta sección.', 'danger')
        return redirect(url_for('main.dashboard'))

    from models_extra.horarios_notificaciones import MATERIAS, MODULOS
    import json

    # Leer configuración persistida (guardada en la tabla ConfigSistema si existe,
    # o en un archivo JSON simple como fallback)
    from models import ConfigSistema

    cfg = ConfigSistema.obtener()

    if request.method == 'POST':
        accion = request.form.get('accion')

        # ── 1. Guardar materias / cargos ────────────────────────────────────
        if accion == 'guardar_materias':
            materias_raw = request.form.get('materias_texto', '')
            nuevas = sorted(set(
                m.strip().upper()
                for m in materias_raw.splitlines()
                if m.strip()
            ))
            cfg.set_materias(nuevas)
            flash(f'Lista de materias actualizada ({len(nuevas)} ítems).', 'success')

        # ── 2. Guardar módulos horarios ─────────────────────────────────────
        elif accion == 'guardar_modulos':
            nuevos_modulos = {}
            for num in range(1, 16):
                inicio = request.form.get(f'mod_{num}_inicio', '').strip()
                fin    = request.form.get(f'mod_{num}_fin', '').strip()
                turno  = request.form.get(f'mod_{num}_turno', '').strip()
                codigo = request.form.get(f'mod_{num}_codigo', '').strip()
                if inicio and fin and turno and codigo:
                    nuevos_modulos[num] = (inicio, fin, turno, codigo)
            cfg.set_modulos(nuevos_modulos)
            flash('Horarios de módulos actualizados.', 'success')

        # ── 3. Guardar templates de mail ────────────────────────────────────
        elif accion == 'guardar_mails':
            cfg.mail_retiro_carro     = request.form.get('mail_retiro_carro', '').strip()
            cfg.mail_devolucion_carro = request.form.get('mail_devolucion_carro', '').strip()
            cfg.mail_retiro_nb        = request.form.get('mail_retiro_nb', '').strip()
            cfg.mail_devolucion_nb    = request.form.get('mail_devolucion_nb', '').strip()
            cfg.guardar()
            flash('Templates de mail actualizados.', 'success')

        return redirect(url_for('main.config_sistema'))

    # GET — preparar datos para el template
    materias_actuales = cfg.get_materias() or MATERIAS
    modulos_actuales  = cfg.get_modulos()  or MODULOS

    # Defaults de mail si no están configurados
    mail_retiro_carro     = cfg.mail_retiro_carro     or _mail_default_retiro_carro()
    mail_devolucion_carro = cfg.mail_devolucion_carro or _mail_default_devolucion_carro()
    mail_retiro_nb        = cfg.mail_retiro_nb        or _mail_default_retiro_nb()
    mail_devolucion_nb    = cfg.mail_devolucion_nb    or _mail_default_devolucion_nb()

    return render_template(
        'main/config_sistema.html',
        materias=materias_actuales,
        modulos=modulos_actuales,
        mail_retiro_carro=mail_retiro_carro,
        mail_devolucion_carro=mail_devolucion_carro,
        mail_retiro_nb=mail_retiro_nb,
        mail_devolucion_nb=mail_devolucion_nb,
    )


def _mail_default_retiro_carro():
    return """Retiro de carro

Docente:   {docente}
Carro:     {carro}
Aula:      {aula}
Hora:      {hora}
Registró:  {encargado}"""


def _mail_default_devolucion_carro():
    return """Devolución de carro

Docente:    {docente}
Carro:      {carro}
Retiro:     {hora_retiro}
Devolución: {hora_devolucion}
Duración:   {duracion}
Registró:   {encargado}"""


def _mail_default_retiro_nb():
    return """Retiro de netbooks

Docente:   {docente}
Hora:      {hora}
Registró:  {encargado}

Netbooks:
{items}"""


def _mail_default_devolucion_nb():
    return """Devolución de netbooks

Docente:    {docente}
Retiro:     {hora_retiro}
Devolución: {hora_devolucion}
Duración:   {duracion}
Registró:   {encargado}
Netbooks:   {cantidad}"""
