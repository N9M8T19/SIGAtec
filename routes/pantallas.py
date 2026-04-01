from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from models import db, PantallaDigital, HistorialPantalla
from datetime import datetime

pantallas_bp = Blueprint('pantallas', __name__, url_prefix='/pantallas')


@pantallas_bp.route('/')
@login_required
def index():
    filtro    = request.args.get('filtro', 'todas')
    busqueda  = request.args.get('q', '').strip()

    query = PantallaDigital.query

    if filtro == 'operativas':
        query = query.filter_by(estado='operativa')
    elif filtro == 'servicio':
        query = query.filter_by(estado='servicio_tecnico')
    elif filtro == 'baja':
        query = query.filter_by(estado='baja')

    if busqueda:
        query = query.filter(
            db.or_(
                PantallaDigital.aula.ilike(f'%{busqueda}%'),
                PantallaDigital.numero_serie.ilike(f'%{busqueda}%'),
                PantallaDigital.marca.ilike(f'%{busqueda}%'),
            )
        )

    pantallas = query.order_by(PantallaDigital.aula).all()

    # Contadores para el resumen
    total       = PantallaDigital.query.count()
    operativas  = PantallaDigital.query.filter_by(estado='operativa').count()
    en_servicio = PantallaDigital.query.filter_by(estado='servicio_tecnico').count()
    de_baja     = PantallaDigital.query.filter_by(estado='baja').count()

    return render_template('pantallas/index.html',
                           pantallas=pantallas, filtro=filtro,
                           busqueda=busqueda,
                           total=total, operativas=operativas,
                           en_servicio=en_servicio, de_baja=de_baja)


@pantallas_bp.route('/nueva', methods=['GET', 'POST'])
@login_required
def nueva():
    if not current_user.tiene_permiso('configuracion'):
        flash('Credenciales no válidas para esta acción.', 'danger')
        return redirect(url_for('pantallas.index'))

    if request.method == 'POST':
        numero_serie = request.form.get('numero_serie', '').strip()

        if PantallaDigital.query.filter_by(numero_serie=numero_serie).first():
            flash(f'Ya existe una pantalla con el número de serie {numero_serie}.', 'danger')
            return redirect(url_for('pantallas.nueva'))

        pantalla = PantallaDigital(
            aula         = request.form.get('aula', '').strip(),
            numero_serie = numero_serie,
            marca        = request.form.get('marca', '').strip(),
            modelo       = request.form.get('modelo', '').strip(),
            observaciones= request.form.get('observaciones', '').strip(),
        )
        db.session.add(pantalla)
        db.session.flush()

        # Registrar alta en historial
        h = HistorialPantalla(
            pantalla_id = pantalla.id,
            evento      = 'alta',
            descripcion = 'Alta de pantalla en el sistema.',
            usuario     = current_user.nombre_completo
        )
        db.session.add(h)
        db.session.commit()
        flash(f'Pantalla del {pantalla.display} agregada correctamente.', 'success')
        return redirect(url_for('pantallas.index'))

    return render_template('pantallas/form.html', pantalla=None)


@pantallas_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    pantalla = PantallaDigital.query.get_or_404(id)

    if request.method == 'POST':
        pantalla.aula          = request.form.get('aula', '').strip()
        pantalla.marca         = request.form.get('marca', '').strip()
        pantalla.modelo        = request.form.get('modelo', '').strip()
        pantalla.observaciones = request.form.get('observaciones', '').strip()
        db.session.commit()
        flash(f'Pantalla del {pantalla.display} actualizada.', 'success')
        return redirect(url_for('pantallas.index'))

    return render_template('pantallas/form.html', pantalla=pantalla)


@pantallas_bp.route('/<int:id>/servicio', methods=['POST'])
@login_required
def marcar_servicio(id):
    pantalla = PantallaDigital.query.get_or_404(id)
    problema = request.form.get('problema', '').strip()

    pantalla.estado         = 'servicio_tecnico'
    pantalla.problema       = problema
    pantalla.fecha_problema = datetime.utcnow()

    h = HistorialPantalla(
        pantalla_id = pantalla.id,
        evento      = 'servicio_tecnico',
        descripcion = problema or 'Enviada a servicio técnico.',
        usuario     = current_user.nombre_completo
    )
    db.session.add(h)
    db.session.commit()
    flash(f'Pantalla del {pantalla.display} enviada a servicio técnico.', 'warning')
    return redirect(url_for('pantallas.index'))


@pantallas_bp.route('/<int:id>/reparada', methods=['POST'])
@login_required
def marcar_reparada(id):
    pantalla = PantallaDigital.query.get_or_404(id)
    pantalla.estado         = 'operativa'
    pantalla.problema       = ''
    pantalla.fecha_problema = None

    h = HistorialPantalla(
        pantalla_id = pantalla.id,
        evento      = 'reparada',
        descripcion = 'Pantalla reparada y operativa.',
        usuario     = current_user.nombre_completo
    )
    db.session.add(h)
    db.session.commit()
    flash(f'Pantalla del {pantalla.display} marcada como operativa.', 'success')
    return redirect(url_for('pantallas.index'))


@pantallas_bp.route('/<int:id>/baja', methods=['POST'])
@login_required
def dar_baja(id):
    if not current_user.tiene_permiso('configuracion'):
        flash('Credenciales no válidas.', 'danger')
        return redirect(url_for('pantallas.index'))

    pantalla = PantallaDigital.query.get_or_404(id)
    motivo   = request.form.get('motivo', '').strip()
    pantalla.estado  = 'baja'
    pantalla.problema = motivo

    h = HistorialPantalla(
        pantalla_id = pantalla.id,
        evento      = 'baja',
        descripcion = motivo or 'Dada de baja.',
        usuario     = current_user.nombre_completo
    )
    db.session.add(h)
    db.session.commit()
    flash(f'Pantalla del {pantalla.display} dada de baja.', 'danger')
    return redirect(url_for('pantallas.index'))


@pantallas_bp.route('/<int:id>/historial')
@login_required
def ver_historial(id):
    pantalla = PantallaDigital.query.get_or_404(id)
    return render_template('pantallas/historial.html', pantalla=pantalla)
