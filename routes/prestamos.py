from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from models import db, Carro, Docente, PrestamoCarro, PrestamoNetbook, PrestamoNetbookItem, Netbook, ConfigEspacioDigital
from datetime import datetime
import random, string

prestamos_bp = Blueprint('prestamos', __name__, url_prefix='/prestamos')


def _gen_codigo(prefijo='P'):
    while True:
        codigo = prefijo + ''.join(random.choices(string.digits, k=4))
        if prefijo == 'P':
            if not PrestamoCarro.query.filter_by(codigo=codigo).first():
                return codigo
        else:
            if not PrestamoNetbook.query.filter_by(codigo=codigo).first():
                return codigo


# ─────────────────────────────────────────────────────────────────────────────
#  PRÉSTAMOS DE CARROS
# ─────────────────────────────────────────────────────────────────────────────

@prestamos_bp.route('/carros')
@login_required
def carros():
    prestamos = PrestamoCarro.query.filter_by(estado='activo').all()
    carros    = Carro.query.filter(Carro.estado != 'baja').order_by(Carro.numero_fisico).all()
    return render_template('prestamos/carros.html',
                           prestamos=prestamos, carros=carros)


@prestamos_bp.route('/carros/retiro', methods=['GET', 'POST'])
@login_required
def retiro_carro():
    if request.method == 'POST':
        carro_id   = request.form.get('carro_id')
        docente_id = request.form.get('docente_id')

        carro   = Carro.query.get_or_404(carro_id)
        docente = Docente.query.get_or_404(docente_id)

        # Verificar que no esté prestado
        activo = PrestamoCarro.query.filter_by(carro_id=carro_id, estado='activo').first()
        if activo:
            flash(f'El carro {carro.display} ya esta prestado.', 'danger')
            return redirect(url_for('prestamos.retiro_carro'))

        prestamo = PrestamoCarro(
            codigo           = _gen_codigo('P'),
            docente_id       = docente.id,
            carro_id         = carro.id,
            aula             = carro.aula,
            encargado_retiro = current_user.nombre_completo
        )
        db.session.add(prestamo)
        db.session.commit()
        flash(f'Retiro registrado: {docente.nombre_completo} — {carro.display}', 'success')
        return redirect(url_for('prestamos.carros'))

    carros   = Carro.query.filter(Carro.estado != 'baja').order_by(Carro.numero_fisico).all()
    docentes = Docente.query.filter_by(activo=True).order_by(Docente.apellido).all()
    return render_template('prestamos/retiro_carro.html',
                           carros=carros, docentes=docentes)


@prestamos_bp.route('/carros/<int:id>/devolucion', methods=['POST'])
@login_required
def devolucion_carro(id):
    prestamo = PrestamoCarro.query.get_or_404(id)
    prestamo.hora_devolucion      = datetime.utcnow()
    prestamo.estado               = 'devuelto'
    prestamo.encargado_devolucion = current_user.nombre_completo
    db.session.commit()
    flash(f'Devolucion registrada: {prestamo.docente.nombre_completo} — {prestamo.carro.display}', 'success')
    return redirect(url_for('prestamos.carros'))


# ─────────────────────────────────────────────────────────────────────────────
#  ESPACIO DIGITAL
# ─────────────────────────────────────────────────────────────────────────────

@prestamos_bp.route('/espacio-digital')
@login_required
def espacio_digital():
    config   = ConfigEspacioDigital.query.first()
    carro    = config.carro if config else None
    prestamos = PrestamoNetbook.query.filter_by(estado='activo').all()
    return render_template('prestamos/espacio_digital.html',
                           prestamos=prestamos, carro=carro, config=config)


@prestamos_bp.route('/espacio-digital/retiro', methods=['GET', 'POST'])
@login_required
def retiro_netbooks():
    config = ConfigEspacioDigital.query.first()
    carro  = config.carro if config else None

    if not carro:
        flash('El carro del Espacio Digital no esta configurado.', 'danger')
        return redirect(url_for('prestamos.espacio_digital'))

    if request.method == 'POST':
        docente_id  = request.form.get('docente_id')
        netbook_ids = request.form.getlist('netbook_ids')

        if not docente_id or not netbook_ids:
            flash('Selecciona un docente y al menos una netbook.', 'danger')
            return redirect(url_for('prestamos.retiro_netbooks'))

        docente  = Docente.query.get_or_404(docente_id)
        prestamo = PrestamoNetbook(
            codigo           = _gen_codigo('NB'),
            docente_id       = docente.id,
            encargado_retiro = current_user.nombre_completo
        )
        db.session.add(prestamo)
        db.session.flush()

        for nb_id in netbook_ids:
            nb   = Netbook.query.get(nb_id)
            item = PrestamoNetbookItem(
                prestamo_id    = prestamo.id,
                netbook_id     = nb.id,
                numero_interno = nb.numero_interno,
                numero_serie   = nb.numero_serie,
                alumno         = nb.alumno
            )
            db.session.add(item)

        db.session.commit()
        flash(f'Prestamo registrado: {docente.nombre_completo} — {len(netbook_ids)} netbook(s)', 'success')
        return redirect(url_for('prestamos.espacio_digital'))

    # Netbooks disponibles del carro
    prestadas_ids = {item.netbook_id for p in PrestamoNetbook.query.filter_by(estado='activo').all()
                     for item in p.items}
    disponibles   = [nb for nb in carro.netbooks
                     if nb.estado == 'operativa' and nb.id not in prestadas_ids]
    docentes      = Docente.query.filter_by(activo=True).order_by(Docente.apellido).all()

    return render_template('prestamos/retiro_netbooks.html',
                           docentes=docentes, disponibles=disponibles, carro=carro)


@prestamos_bp.route('/espacio-digital/<int:id>/devolucion', methods=['POST'])
@login_required
def devolucion_netbooks(id):
    prestamo = PrestamoNetbook.query.get_or_404(id)
    prestamo.hora_devolucion      = datetime.utcnow()
    prestamo.estado               = 'devuelto'
    prestamo.encargado_devolucion = current_user.nombre_completo
    db.session.commit()
    flash(f'Devolucion registrada: {prestamo.docente.nombre_completo} — {len(prestamo.items)} netbook(s)', 'success')
    return redirect(url_for('prestamos.espacio_digital'))


# ─────────────────────────────────────────────────────────────────────────────
#  HISTORIAL
# ─────────────────────────────────────────────────────────────────────────────

@prestamos_bp.route('/historial')
@login_required
def historial():
    periodo  = request.args.get('periodo', 'hoy')
    busqueda = request.args.get('q', '').strip()
    tipo     = request.args.get('tipo', 'carros')

    from datetime import timedelta
    ahora = datetime.utcnow()

    if tipo == 'carros':
        query = PrestamoCarro.query
        if periodo == 'hoy':
            query = query.filter(PrestamoCarro.hora_retiro >= ahora.replace(hour=0, minute=0))
        elif periodo == 'semana':
            query = query.filter(PrestamoCarro.hora_retiro >= ahora - timedelta(days=7))
        elif periodo == 'mes':
            query = query.filter(PrestamoCarro.hora_retiro >= ahora - timedelta(days=30))
        if busqueda:
            query = query.join(Docente).filter(
                db.or_(Docente.apellido.ilike(f'%{busqueda}%'),
                       Docente.nombre.ilike(f'%{busqueda}%'),
                       Docente.dni.ilike(f'%{busqueda}%')))
        prestamos = query.order_by(PrestamoCarro.hora_retiro.desc()).all()
    else:
        query = PrestamoNetbook.query
        if periodo == 'hoy':
            query = query.filter(PrestamoNetbook.hora_retiro >= ahora.replace(hour=0, minute=0))
        elif periodo == 'semana':
            query = query.filter(PrestamoNetbook.hora_retiro >= ahora - timedelta(days=7))
        elif periodo == 'mes':
            query = query.filter(PrestamoNetbook.hora_retiro >= ahora - timedelta(days=30))
        if busqueda:
            query = query.join(Docente).filter(
                db.or_(Docente.apellido.ilike(f'%{busqueda}%'),
                       Docente.nombre.ilike(f'%{busqueda}%')))
        prestamos = query.order_by(PrestamoNetbook.hora_retiro.desc()).all()

    return render_template('prestamos/historial.html',
                           prestamos=prestamos, periodo=periodo,
                           busqueda=busqueda, tipo=tipo)
