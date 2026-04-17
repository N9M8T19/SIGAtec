from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Docente, PrestamoCarro, PrestamoNetbook, PrestamoNetbookItem
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


@mantenimiento_bp.route('/limpiar-pruebas')
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

    return render_template(
        'mantenimiento/limpiar_pruebas.html',
        resumen=resumen,
        activos_carros=activos_carros,
        activos_ed=activos_ed,
    )


@mantenimiento_bp.route('/limpiar-pruebas/ejecutar', methods=['POST'])
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

    # ── Modo: todos los activos ──────────────────────────────────────────────
    elif modo == 'activos':
        # Espacio Digital activos
        prestamos_ed_activos = PrestamoNetbook.query.filter_by(estado='activo').all()
        for p in prestamos_ed_activos:
            PrestamoNetbookItem.query.filter_by(prestamo_id=p.id).delete()
        total_ed = PrestamoNetbook.query.filter_by(estado='activo').delete(
            synchronize_session=False
        )
        # Carros activos
        total_carros = PrestamoCarro.query.filter_by(estado='activo').delete(
            synchronize_session=False
        )

    db.session.commit()

    tipo_txt = 'activos' if (solo_activos or modo == 'activos') else 'en total'
    flash(
        f'Limpieza completada ({tipo_txt}): '
        f'{total_carros} préstamo(s) de carros y '
        f'{total_ed} préstamo(s) del Espacio Digital eliminados.',
        'success',
    )
    return redirect(url_for('mantenimiento.limpiar_pruebas'))
