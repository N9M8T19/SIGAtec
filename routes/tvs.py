# routes/tvs.py
"""
Módulo TVs — blueprint Flask.

Registrar en app.py:
    from routes.tvs import tvs_bp
    app.register_blueprint(tvs_bp)
"""

from flask import (Blueprint, render_template, request, redirect,
                   url_for, flash, send_file)
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from io import BytesIO

from models import db, TV, PrestamoTV, Docente
from services.pdf_reportes import pdf_historial_tvs

ARG_OFFSET = timedelta(hours=-3)

tvs_bp = Blueprint('tvs', __name__, url_prefix='/tvs')


def _solo_admin_directivo():
    return current_user.rol in ('Administrador', 'Directivo')


# ── Listado ────────────────────────────────────────────────────────────────────

@tvs_bp.route('/')
@login_required
def index():
    tvs      = TV.query.order_by(TV.numero_interno).all()
    n_activos = PrestamoTV.query.filter_by(estado='activo').count()
    return render_template('tvs/index.html', tvs=tvs, n_activos=n_activos)


# ── Alta ───────────────────────────────────────────────────────────────────────

@tvs_bp.route('/nueva', methods=['GET', 'POST'])
@login_required
def nueva():
    if not _solo_admin_directivo():
        flash('No tenés permiso para registrar televisores.', 'danger')
        return redirect(url_for('tvs.index'))

    if request.method == 'POST':
        f = request.form
        num = int(f['numero_interno'])
        if TV.query.filter_by(numero_interno=num).first():
            flash(f'Ya existe una TV con el número interno {num}.', 'danger')
            return render_template('tvs/form.html', tv=None, accion='nueva')

        tv = TV(
            numero_interno        = num,
            marca                 = f['marca'].strip(),
            modelo                = f['modelo'].strip(),
            numero_serie          = f.get('numero_serie', '').strip() or None,
            pulgadas              = int(f['pulgadas']) if f.get('pulgadas') else None,
            aula                  = f.get('aula', '').strip() or None,
            observaciones         = f.get('observaciones', '').strip() or None,
            tiene_control_remoto  = 'tiene_control_remoto'  in f,
            tiene_cable_hdmi      = 'tiene_cable_hdmi'      in f,
            tiene_cable_vga       = 'tiene_cable_vga'       in f,
            tiene_cable_corriente = 'tiene_cable_corriente' in f,
            tiene_soporte_pared   = 'tiene_soporte_pared'   in f,
            tiene_soporte_pie     = 'tiene_soporte_pie'     in f,
            tiene_chromecast      = 'tiene_chromecast'      in f,
            tiene_adaptador_hdmi  = 'tiene_adaptador_hdmi'  in f,
            componentes_extra     = f.get('componentes_extra', '').strip() or None,
        )
        db.session.add(tv)
        db.session.commit()
        flash(f'{tv.codigo} registrada correctamente.', 'success')
        return redirect(url_for('tvs.index'))

    return render_template('tvs/form.html', tv=None, accion='nueva')


# ── Editar ─────────────────────────────────────────────────────────────────────

@tvs_bp.route('/<int:tv_id>/editar', methods=['GET', 'POST'])
@login_required
def editar(tv_id):
    if not _solo_admin_directivo():
        flash('No tenés permiso para editar televisores.', 'danger')
        return redirect(url_for('tvs.index'))

    tv = TV.query.get_or_404(tv_id)

    if request.method == 'POST':
        f = request.form
        tv.marca                 = f['marca'].strip()
        tv.modelo                = f['modelo'].strip()
        tv.numero_serie          = f.get('numero_serie', '').strip() or None
        tv.pulgadas              = int(f['pulgadas']) if f.get('pulgadas') else None
        tv.aula                  = f.get('aula', '').strip() or None
        tv.observaciones         = f.get('observaciones', '').strip() or None
        tv.tiene_control_remoto  = 'tiene_control_remoto'  in f
        tv.tiene_cable_hdmi      = 'tiene_cable_hdmi'      in f
        tv.tiene_cable_vga       = 'tiene_cable_vga'       in f
        tv.tiene_cable_corriente = 'tiene_cable_corriente' in f
        tv.tiene_soporte_pared   = 'tiene_soporte_pared'   in f
        tv.tiene_soporte_pie     = 'tiene_soporte_pie'     in f
        tv.tiene_chromecast      = 'tiene_chromecast'      in f
        tv.tiene_adaptador_hdmi  = 'tiene_adaptador_hdmi'  in f
        tv.componentes_extra     = f.get('componentes_extra', '').strip() or None
        db.session.commit()
        flash(f'{tv.codigo} actualizada.', 'success')
        return redirect(url_for('tvs.index'))

    return render_template('tvs/form.html', tv=tv, accion='editar')


# ── Servicio técnico ───────────────────────────────────────────────────────────

@tvs_bp.route('/<int:tv_id>/servicio', methods=['POST'])
@login_required
def enviar_servicio(tv_id):
    tv = TV.query.get_or_404(tv_id)
    motivo = request.form.get('motivo_servicio', '').strip()
    if not motivo:
        flash('Indicá el motivo del servicio técnico.', 'warning')
        return redirect(url_for('tvs.index'))
    tv.estado          = 'en_servicio'
    tv.motivo_servicio = motivo
    tv.fecha_servicio  = datetime.utcnow()
    db.session.commit()
    flash(f'{tv.codigo} enviada a servicio técnico.', 'warning')
    return redirect(url_for('tvs.index'))


@tvs_bp.route('/<int:tv_id>/recuperar', methods=['POST'])
@login_required
def recuperar(tv_id):
    tv = TV.query.get_or_404(tv_id)
    tv.estado          = 'disponible'
    tv.motivo_servicio = None
    tv.fecha_servicio  = None
    db.session.commit()
    flash(f'{tv.codigo} recuperada del servicio técnico.', 'success')
    return redirect(url_for('tvs.index'))


# ── Baja ───────────────────────────────────────────────────────────────────────

@tvs_bp.route('/<int:tv_id>/baja', methods=['POST'])
@login_required
def baja(tv_id):
    if not _solo_admin_directivo():
        flash('No tenés permiso para dar de baja televisores.', 'danger')
        return redirect(url_for('tvs.index'))
    tv = TV.query.get_or_404(tv_id)
    tv.estado = 'de_baja'
    db.session.commit()
    flash(f'{tv.codigo} dada de baja.', 'secondary')
    return redirect(url_for('tvs.index'))


# ── Préstamo: retiro ───────────────────────────────────────────────────────────

@tvs_bp.route('/<int:tv_id>/prestar', methods=['GET', 'POST'])
@login_required
def prestar(tv_id):
    tv = TV.query.get_or_404(tv_id)
    if tv.estado != 'disponible':
        flash(f'{tv.codigo} no está disponible para préstamo.', 'danger')
        return redirect(url_for('tvs.index'))

    docentes = Docente.query.filter_by(activo=True).order_by(Docente.apellido).all()

    if request.method == 'POST':
        f = request.form
        horas = int(f['horas_esperadas']) if f.get('horas_esperadas') else None
        p = PrestamoTV(
            tv_id                    = tv.id,
            docente_id               = int(f['docente_id']) if f.get('docente_id') else None,
            nombre_solicitante       = f.get('nombre_solicitante', '').strip() or None,
            aula_destino             = f.get('aula_destino', '').strip() or None,
            motivo                   = f.get('motivo', '').strip() or None,
            fecha_retiro             = datetime.utcnow(),
            fecha_devolucion_esperada= datetime.utcnow() + timedelta(hours=horas) if horas else None,
            encargado_retiro_id      = current_user.id,
            estado                   = 'activo',
        )
        tv.estado = 'prestada'
        db.session.add(p)
        db.session.commit()
        flash(f'Préstamo de {tv.codigo} registrado.', 'success')
        return redirect(url_for('tvs.prestamos_activos'))

    return render_template('tvs/prestar.html', tv=tv, docentes=docentes)


# ── Préstamo: devolución ───────────────────────────────────────────────────────

@tvs_bp.route('/prestamo/<int:prestamo_id>/devolver', methods=['GET', 'POST'])
@login_required
def devolver(prestamo_id):
    p  = PrestamoTV.query.get_or_404(prestamo_id)
    tv = p.tv

    if request.method == 'POST':
        f = request.form
        p.fecha_devolucion_real     = datetime.utcnow()
        p.encargado_devolucion_id   = current_user.id
        p.estado                    = 'devuelto'
        p.observaciones             = f.get('observaciones', '').strip() or None
        p.devuelto_control_remoto   = 'devuelto_control_remoto'  in f
        p.devuelto_cable_hdmi       = 'devuelto_cable_hdmi'      in f
        p.devuelto_cable_vga        = 'devuelto_cable_vga'       in f
        p.devuelto_cable_corriente  = 'devuelto_cable_corriente' in f
        p.devuelto_soporte_pared    = 'devuelto_soporte_pared'   in f
        p.devuelto_soporte_pie      = 'devuelto_soporte_pie'     in f
        p.devuelto_chromecast       = 'devuelto_chromecast'      in f
        p.devuelto_adaptador_hdmi   = 'devuelto_adaptador_hdmi'  in f
        tv.estado = 'disponible'
        db.session.commit()
        flash(f'Devolución de {tv.codigo} registrada.', 'success')
        return redirect(url_for('tvs.prestamos_activos'))

    return render_template('tvs/devolver.html', prestamo=p, tv=tv)


# ── Préstamos activos ──────────────────────────────────────────────────────────

@tvs_bp.route('/prestamos')
@login_required
def prestamos_activos():
    prestamos      = (PrestamoTV.query
                      .filter_by(estado='activo')
                      .order_by(PrestamoTV.fecha_retiro)
                      .all())
    todas_las_tvs  = TV.query.filter(TV.estado != 'de_baja').order_by(TV.numero_interno).all()
    ahora          = datetime.utcnow()
    return render_template('tvs/prestamos.html',
                           prestamos=prestamos,
                           todas_las_tvs=todas_las_tvs,
                           ahora=ahora)


# ── Historial ──────────────────────────────────────────────────────────────────

@tvs_bp.route('/historial')
@login_required
def historial():
    page = request.args.get('page', 1, type=int)
    pag  = (PrestamoTV.query
            .order_by(PrestamoTV.fecha_retiro.desc())
            .paginate(page=page, per_page=50, error_out=False))
    return render_template('tvs/historial.html', paginacion=pag)


@tvs_bp.route('/historial/pdf')
@login_required
def historial_pdf():
    prestamos = PrestamoTV.query.order_by(PrestamoTV.fecha_retiro.desc()).all()
    buf = pdf_historial_tvs(prestamos)
    return send_file(BytesIO(buf), mimetype='application/pdf',
                     download_name='historial_tvs.pdf', as_attachment=True)


# ── Etiquetas ─────────────────────────────────────────────────────────────────

@tvs_bp.route('/etiquetas')
@login_required
def etiquetas():
    return redirect(url_for('etiquetas.tvs'))
