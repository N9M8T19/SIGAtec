from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from models import db, Netbook, Carro

etiquetas_bp = Blueprint('etiquetas', __name__, url_prefix='/etiquetas')


@etiquetas_bp.route('/')
@login_required
def index():
    carros = Carro.query.filter(Carro.estado != 'baja').order_by(Carro.numero_fisico).all()
    return render_template('etiquetas/index.html', carros=carros)


@etiquetas_bp.route('/api/datos')
@login_required
def datos():
    carro_id = request.args.get('carro_id', type=int)

    query = Netbook.query.join(Carro).filter(Carro.estado != 'baja')
    if carro_id:
        query = query.filter(Netbook.carro_id == carro_id)

    netbooks = query.all()

    # Ordenamiento numérico correcto — igual que pdf_reportes.py
    # .zfill(10) evita orden textual (1, 10, 11, 2...) documentado en bitácora
    netbooks = sorted(netbooks, key=lambda n: (
        str(n.carro.numero_fisico or '').zfill(10),
        str(n.numero_interno or '').zfill(10)
    ))

    resultado = []
    for n in netbooks:
        tm = n.alumno_manana
        tt = n.alumno_tarde
        resultado.append({
            'id':             n.id,
            'numero_interno': n.numero_interno or '',
            'numero_serie':   n.numero_serie or '',
            'carro':          f'Carro {n.carro.numero_fisico}' if n.carro and n.carro.numero_fisico else f'Carro {n.carro_id}',
            'carro_id':       n.carro_id,
            'aula':           n.carro.aula or '' if n.carro else '',
            'alumno_manana':  f'{tm.apellido}, {tm.nombre}' if tm else '',
            'alumno_tarde':   f'{tt.apellido}, {tt.nombre}' if tt else '',
            'curso_manana':   tm.curso if tm else '',
            'curso_tarde':    tt.curso if tt else '',
        })

    return jsonify(resultado)
