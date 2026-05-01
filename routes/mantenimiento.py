from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, Docente, PrestamoCarro, PrestamoNetbook, PrestamoNetbookItem, PrestamoTV
from functools import wraps

mantenimiento_bp = Blueprint('mantenimiento', __name__, url_prefix='/mantenimiento')


def solo_admin_directivo(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if current_user.rol not in ('Administrador', 'Directivo'):
            flash('No tenés permisos para acceder a esta sección.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated


@mantenimiento_bp.route('/administrar-historial')
@login_required
@solo_admin_directivo
def limpiar_pruebas():
    # ── Resumen por docente ──────────────────────────────────────────────────
    docentes_con_registros = (
        db.session.query(Docente)
        .filter(
            db.or_(
                Docente.id.in_(
                    db.session.query(PrestamoCarro.docente_id).distinct()
                ),
                Docente.id.in_(
                    db.session.query(PrestamoNetbook.docente_id).distinct()
                ),
            )
        )
        .order_by(Docente.apellido, Docente.nombre)
        .all()
    )

    resumen = []
    for d in docentes_con_registros:
        cant_carros_total  = PrestamoCarro.query.filter_by(docente_id=d.id).count()
        cant_carros_activo = PrestamoCarro.query.filter_by(docente_id=d.id, estado='activo').count()
        cant_ed_total      = PrestamoNetbook.query.filter_by(docente_id=d.id).count()
        cant_ed_activo     = PrestamoNetbook.query.filter_by(docente_id=d.id, estado='activo').count()
        resumen.append({
            'docente':           d,
            'carros_total':      cant_carros_total,
            'carros_activos':    cant_carros_activo,
            'ed_total':          cant_ed_total,
            'ed_activos':        cant_ed_activo,
            'total':             cant_carros_total + cant_ed_total,
            'total_activos':     cant_carros_activo + cant_ed_activo,
        })

    # ── Totales globales de activos (sección 2) ──────────────────────────────
    activos_carros = PrestamoCarro.query.filter_by(estado='activo').count()
    activos_ed     = PrestamoNetbook.query.filter_by(estado='activo').count()
    activos_tvs    = PrestamoTV.query.filter_by(estado='activo').count()

    return render_template(
        'mantenimiento/limpiar_pruebas.html',
        resumen=resumen,
        activos_carros=activos_carros,
        activos_ed=activos_ed,
        activos_tvs=activos_tvs,
    )


@mantenimiento_bp.route('/administrar-historial/ejecutar', methods=['POST'])
@login_required
@solo_admin_directivo
def ejecutar_limpieza():
    confirmacion = request.form.get('confirmacion', '').strip()
    if confirmacion != 'CONFIRMAR':
        flash('Escribí CONFIRMAR para ejecutar la limpieza.', 'warning')
        return redirect(url_for('mantenimiento.limpiar_pruebas'))

    modo        = request.form.get('modo', 'docente')   # 'docente' | 'activos'
    solo_activos = request.form.get('solo_activos') == '1'
    docente_ids  = request.form.getlist('docente_ids')

    total_carros = 0
    total_ed     = 0
    total_tvs    = 0

    # ── Modo: por docente ────────────────────────────────────────────────────
    if modo == 'docente':
        if not docente_ids:
            flash('No seleccionaste ningún docente.', 'warning')
            return redirect(url_for('mantenimiento.limpiar_pruebas'))

        for did in docente_ids:
            # Espacio Digital
            q_ed = PrestamoNetbook.query.filter_by(docente_id=did)
            if solo_activos:
                q_ed = q_ed.filter_by(estado='activo')
            for p in q_ed.all():
                PrestamoNetbookItem.query.filter_by(prestamo_id=p.id).delete()
            total_ed += q_ed.delete(synchronize_session=False)

            # Carros
            q_carros = PrestamoCarro.query.filter_by(docente_id=did)
            if solo_activos:
                q_carros = q_carros.filter_by(estado='activo')
            total_carros += q_carros.delete(synchronize_session=False)

            # TVs
            q_tvs = PrestamoTV.query.filter_by(docente_id=did)
            if solo_activos:
                q_tvs = q_tvs.filter_by(estado='activo')
            total_tvs += q_tvs.delete(synchronize_session=False)

    # ── Modo: todos los activos ──────────────────────────────────────────────
    elif modo == 'activos':
        prestamos_ed_activos = PrestamoNetbook.query.filter_by(estado='activo').all()
        for p in prestamos_ed_activos:
            PrestamoNetbookItem.query.filter_by(prestamo_id=p.id).delete()
        total_ed = PrestamoNetbook.query.filter_by(estado='activo').delete(
            synchronize_session=False
        )
        total_carros = PrestamoCarro.query.filter_by(estado='activo').delete(
            synchronize_session=False
        )
        total_tvs = PrestamoTV.query.filter_by(estado='activo').delete(
            synchronize_session=False
        )

    db.session.commit()

    tipo_txt = 'activos' if (solo_activos or modo == 'activos') else 'en total'
    partes = [
        f'{total_carros} préstamo(s) de carros',
        f'{total_ed} préstamo(s) del Espacio Digital',
        f'{total_tvs} préstamo(s) de TVs',
    ]
    flash(f'Limpieza completada ({tipo_txt}): ' + ' y '.join(partes) + ' eliminados.', 'success')
    return redirect(url_for('mantenimiento.limpiar_pruebas'))


# ── Sección 3: préstamos de un docente específico ────────────────────────────

@mantenimiento_bp.route('/administrar-historial/prestamos-docente')
@login_required
@solo_admin_directivo
def prestamos_docente():
    """Devuelve JSON con todos los préstamos de un docente para la Sección 3."""
    docente_id = request.args.get('docente_id', type=int)
    if not docente_id:
        return jsonify({'carros': [], 'ed': []})

    from datetime import timedelta
    ARG_OFFSET = timedelta(hours=-3)

    def fmt(dt):
        if dt is None:
            return '—'
        return (dt + ARG_OFFSET).strftime('%d/%m/%Y %H:%M')

    carros = PrestamoCarro.query.filter_by(docente_id=docente_id)\
                .order_by(PrestamoCarro.hora_retiro.desc()).all()
    ed     = PrestamoNetbook.query.filter_by(docente_id=docente_id)\
                .order_by(PrestamoNetbook.hora_retiro.desc()).all()

    carros_data = []
    for p in carros:
        carros_data.append({
            'id':             p.id,
            'codigo':         p.codigo if hasattr(p, 'codigo') and p.codigo else f'#{p.id}',
            'carro':          p.carro.display if p.carro else '—',
            'aula':           p.carro.aula if p.carro else '—',
            'fecha_retiro':   fmt(p.hora_retiro),
            'fecha_devolucion': fmt(p.hora_devolucion) if p.hora_devolucion else None,
            'estado':         p.estado,
        })

    ed_data = []
    for p in ed:
        cant = len(p.items) if hasattr(p, 'items') else 0
        ed_data.append({
            'id':               p.id,
            'fecha_retiro':     fmt(p.hora_retiro),
            'fecha_devolucion': fmt(p.hora_devolucion) if p.hora_devolucion else None,
            'estado':           p.estado,
            'cant_netbooks':    cant,
        })

    tvs_data = []
    tvs_qs = PrestamoTV.query.filter_by(docente_id=docente_id)\
                .order_by(PrestamoTV.fecha_retiro.desc()).all()
    for p in tvs_qs:
        tvs_data.append({
            'id':               p.id,
            'tv':               p.tv.codigo if p.tv else '—',
            'aula_destino':     p.aula_destino or '—',
            'fecha_retiro':     fmt(p.fecha_retiro),
            'fecha_devolucion': fmt(p.fecha_devolucion_real) if p.fecha_devolucion_real else None,
            'estado':           p.estado,
        })

    return jsonify({'carros': carros_data, 'ed': ed_data, 'tvs': tvs_data})


@mantenimiento_bp.route('/administrar-historial/borrar-prestamos', methods=['POST'])
@login_required
@solo_admin_directivo
def borrar_prestamos_individuales():
    """Borra préstamos individuales seleccionados en la Sección 3."""
    confirmacion = request.form.get('confirmacion', '').strip()
    if confirmacion != 'CONFIRMAR':
        flash('Escribí CONFIRMAR para ejecutar la limpieza.', 'warning')
        return redirect(url_for('mantenimiento.limpiar_pruebas'))

    ids_carros = request.form.getlist('ids_carros')
    ids_ed     = request.form.getlist('ids_ed')
    ids_tvs    = request.form.getlist('ids_tvs')

    if not ids_carros and not ids_ed and not ids_tvs:
        flash('No seleccionaste ningún préstamo.', 'warning')
        return redirect(url_for('mantenimiento.limpiar_pruebas'))

    total_carros = 0
    total_ed     = 0
    total_tvs    = 0

    for pid in ids_carros:
        deleted = PrestamoCarro.query.filter_by(id=pid).delete()
        total_carros += deleted

    for pid in ids_ed:
        PrestamoNetbookItem.query.filter_by(prestamo_id=pid).delete()
        deleted = PrestamoNetbook.query.filter_by(id=pid).delete()
        total_ed += deleted

    for pid in ids_tvs:
        deleted = PrestamoTV.query.filter_by(id=pid).delete()
        total_tvs += deleted

    db.session.commit()

    partes = []
    if total_carros: partes.append(f'{total_carros} préstamo(s) de carros')
    if total_ed:     partes.append(f'{total_ed} préstamo(s) del Espacio Digital')
    if total_tvs:    partes.append(f'{total_tvs} préstamo(s) de TVs')
    flash('Eliminados: ' + ', '.join(partes) + '.', 'success')
    return redirect(url_for('mantenimiento.limpiar_pruebas'))
