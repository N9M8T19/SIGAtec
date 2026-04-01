from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, PrestamoCarro, PrestamoNetbook, Docente, Carro
from datetime import datetime, timedelta

reportes_bp = Blueprint('reportes', __name__, url_prefix='/reportes')


def _filtrar_prestamos_carros(periodo, fecha_desde=None, fecha_hasta=None):
    ahora = datetime.utcnow()
    query = PrestamoCarro.query

    if fecha_desde and fecha_hasta:
        try:
            d_desde  = datetime.strptime(fecha_desde, '%Y-%m-%d')
            d_hasta  = datetime.strptime(fecha_hasta, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
            query    = query.filter(PrestamoCarro.hora_retiro >= d_desde,
                                    PrestamoCarro.hora_retiro <= d_hasta)
        except ValueError:
            pass
    elif fecha_desde:
        try:
            d_desde = datetime.strptime(fecha_desde, '%Y-%m-%d')
            query   = query.filter(PrestamoCarro.hora_retiro >= d_desde)
        except ValueError:
            pass
    elif periodo == 'hoy':
        query = query.filter(PrestamoCarro.hora_retiro >= ahora.replace(hour=0, minute=0, second=0))
    elif periodo == 'semana':
        query = query.filter(PrestamoCarro.hora_retiro >= ahora - timedelta(days=7))
    elif periodo == 'mes':
        query = query.filter(PrestamoCarro.hora_retiro >= ahora - timedelta(days=30))

    return query.order_by(PrestamoCarro.hora_retiro.desc()).all()


def _filtrar_prestamos_netbooks(periodo, fecha_desde=None, fecha_hasta=None):
    ahora = datetime.utcnow()
    query = PrestamoNetbook.query

    if fecha_desde and fecha_hasta:
        try:
            d_desde = datetime.strptime(fecha_desde, '%Y-%m-%d')
            d_hasta = datetime.strptime(fecha_hasta, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
            query   = query.filter(PrestamoNetbook.hora_retiro >= d_desde,
                                   PrestamoNetbook.hora_retiro <= d_hasta)
        except ValueError:
            pass
    elif fecha_desde:
        try:
            d_desde = datetime.strptime(fecha_desde, '%Y-%m-%d')
            query   = query.filter(PrestamoNetbook.hora_retiro >= d_desde)
        except ValueError:
            pass
    elif periodo == 'hoy':
        query = query.filter(PrestamoNetbook.hora_retiro >= ahora.replace(hour=0, minute=0, second=0))
    elif periodo == 'semana':
        query = query.filter(PrestamoNetbook.hora_retiro >= ahora - timedelta(days=7))
    elif periodo == 'mes':
        query = query.filter(PrestamoNetbook.hora_retiro >= ahora - timedelta(days=30))

    return query.order_by(PrestamoNetbook.hora_retiro.desc()).all()


@reportes_bp.route('/')
@login_required
def index():
    if not current_user.tiene_permiso('reportes'):
        flash('Credenciales no válidas para acceder a reportes.', 'danger')
        return redirect(url_for('main.dashboard'))
    return render_template('reportes/index.html')


@reportes_bp.route('/estadisticas')
@login_required
def estadisticas():
    if not current_user.tiene_permiso('estadisticas'):
        flash('Credenciales no válidas para ver estadísticas.', 'danger')
        return redirect(url_for('main.dashboard'))

    from sqlalchemy import func
    top_docentes = db.session.query(
        Docente, func.count(PrestamoCarro.id).label('total')
    ).join(PrestamoCarro).group_by(Docente.id).order_by(
        func.count(PrestamoCarro.id).desc()).limit(10).all()

    top_materias = db.session.query(
        Docente.materia, func.count(PrestamoCarro.id).label('total')
    ).join(PrestamoCarro).group_by(Docente.materia).order_by(
        func.count(PrestamoCarro.id).desc()).limit(10).all()

    return render_template('reportes/estadisticas.html',
                           top_docentes=top_docentes,
                           top_materias=top_materias)


# ─────────────────────────────────────────────────────────────────────────────
#  PDFs
# ─────────────────────────────────────────────────────────────────────────────

@reportes_bp.route('/pdf/carros')
@login_required
def pdf_carros():
    from services.pdf_reportes import pdf_listado_carros
    carros = Carro.query.filter(Carro.estado != 'baja').order_by(Carro.numero_fisico).all()
    return pdf_listado_carros(carros)


@reportes_bp.route('/pdf/carro/<int:id>')
@login_required
def pdf_netbooks_carro(id):
    from services.pdf_reportes import pdf_netbooks_por_carro
    carro = Carro.query.get_or_404(id)
    return pdf_netbooks_por_carro(carro)


@reportes_bp.route('/pdf/asignadas')
@login_required
def pdf_asignadas():
    from services.pdf_reportes import pdf_netbooks_asignadas
    carro_id = request.args.get('carro_id', type=int)
    if carro_id:
        carro = Carro.query.get_or_404(carro_id)
        return pdf_netbooks_asignadas(carro)
    return pdf_netbooks_asignadas()


@reportes_bp.route('/pdf/servicio-tecnico')
@login_required
def pdf_servicio():
    from services.pdf_reportes import pdf_servicio_tecnico
    return pdf_servicio_tecnico()


@reportes_bp.route('/pdf/historial-carros')
@login_required
def pdf_hist_carros():
    from services.pdf_reportes import pdf_historial_carros
    periodo     = request.args.get('periodo', 'todos')
    fecha_desde = request.args.get('fecha_desde', '')
    fecha_hasta = request.args.get('fecha_hasta', '')
    prestamos   = _filtrar_prestamos_carros(periodo, fecha_desde, fecha_hasta)
    label       = f'{fecha_desde} al {fecha_hasta}' if fecha_desde else periodo
    return pdf_historial_carros(prestamos, label)


@reportes_bp.route('/pdf/historial-netbooks')
@login_required
def pdf_hist_netbooks():
    from services.pdf_reportes import pdf_historial_netbooks
    periodo     = request.args.get('periodo', 'todos')
    fecha_desde = request.args.get('fecha_desde', '')
    fecha_hasta = request.args.get('fecha_hasta', '')
    prestamos   = _filtrar_prestamos_netbooks(periodo, fecha_desde, fecha_hasta)
    label       = f'{fecha_desde} al {fecha_hasta}' if fecha_desde else periodo
    return pdf_historial_netbooks(prestamos, label)


@reportes_bp.route('/pdf/estadisticas')
@login_required
def pdf_estadisticas():
    if not current_user.tiene_permiso('estadisticas'):
        flash('Credenciales no válidas.', 'danger')
        return redirect(url_for('main.dashboard'))
    from services.pdf_reportes import pdf_estadisticas
    from sqlalchemy import func
    top_docentes = db.session.query(
        Docente, func.count(PrestamoCarro.id).label('total')
    ).join(PrestamoCarro).group_by(Docente.id).order_by(
        func.count(PrestamoCarro.id).desc()).limit(10).all()
    top_materias = db.session.query(
        Docente.materia, func.count(PrestamoCarro.id).label('total')
    ).join(PrestamoCarro).group_by(Docente.materia).order_by(
        func.count(PrestamoCarro.id).desc()).limit(10).all()
    return pdf_estadisticas(top_docentes, top_materias)


@reportes_bp.route('/pdf/asignaciones/carro/<int:carro_id>')
@login_required
def pdf_asignaciones_carro(carro_id):
    """PDF con todas las netbooks del carro y sus alumnos asignados."""
    from services.pdf_reportes import generar_pdf_asignaciones_carro
    from flask import send_file
    carro  = Carro.query.get_or_404(carro_id)
    buffer = generar_pdf_asignaciones_carro(carro)
    nombre = f'asignaciones_carro_{carro.numero_fisico}.pdf'
    return send_file(buffer, mimetype='application/pdf',
                     as_attachment=True, download_name=nombre)


@reportes_bp.route('/pdf/asignaciones/netbook/<int:netbook_id>')
@login_required
def pdf_asignacion_netbook(netbook_id):
    """PDF de una netbook individual con su alumno asignado."""
    from services.pdf_reportes import generar_pdf_asignacion_netbook
    from models import Netbook
    from flask import send_file
    netbook = Netbook.query.get_or_404(netbook_id)
    buffer  = generar_pdf_asignacion_netbook(netbook)
    nombre  = f'asignacion_netbook_{netbook.numero_interno}.pdf'
    return send_file(buffer, mimetype='application/pdf',
                     as_attachment=True, download_name=nombre)

@reportes_bp.route('/pdf/inventario/carro/<int:carro_id>')
@login_required
def pdf_inventario_carro(carro_id):
    """PDF simple con N° interno y N° serie de todas las netbooks del carro."""
    from services.pdf_reportes import pdf_inventario_carro
    from flask import send_file
    carro  = Carro.query.get_or_404(carro_id)
    buffer = pdf_inventario_carro(carro)
    nombre = f'inventario_carro_{carro.numero_fisico}.pdf'
    return send_file(buffer, mimetype='application/pdf',
                     as_attachment=True, download_name=nombre)

