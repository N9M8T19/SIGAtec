# routes/etiquetas.py — VERSIÓN COMPLETA
# Reemplaza el archivo existente. Agrega endpoints para TVs, Pantallas e Impresoras.

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from models import db, Netbook, Carro, TV, PantallaDigital, Impresora3D

etiquetas_bp = Blueprint('etiquetas', __name__, url_prefix='/etiquetas')


# ── Netbooks (existente, sin cambios) ─────────────────────────────────────────

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


# ── TVs ───────────────────────────────────────────────────────────────────────

@etiquetas_bp.route('/tvs')
@login_required
def tvs():
    return render_template('etiquetas/tvs.html')


@etiquetas_bp.route('/api/tvs')
@login_required
def api_tvs():
    tvs = TV.query.filter(TV.estado != 'de_baja').order_by(TV.numero_interno).all()
    resultado = []
    for tv in tvs:
        resultado.append({
            'id':             tv.id,
            'codigo':         tv.codigo,              # TV-01
            'numero_interno': tv.numero_interno,
            'marca':          tv.marca or '',
            'modelo':         tv.modelo or '',
            'numero_serie':   tv.numero_serie or '',
            'pulgadas':       f'{tv.pulgadas}"' if tv.pulgadas else '',
            'aula':           tv.aula or '',
            'estado':         tv.estado,
            'componentes':    ', '.join(tv.componentes_lista) if tv.componentes_lista else '',
        })
    return jsonify(resultado)


# ── Pantallas Digitales ───────────────────────────────────────────────────────

@etiquetas_bp.route('/pantallas')
@login_required
def pantallas():
    return render_template('etiquetas/pantallas.html')


@etiquetas_bp.route('/api/pantallas')
@login_required
def api_pantallas():
    pantallas = PantallaDigital.query.filter(
        PantallaDigital.estado != 'baja'
    ).order_by(PantallaDigital.aula).all()
    resultado = []
    for p in pantallas:
        resultado.append({
            'id':           p.id,
            'codigo':       f'PD-{p.id:02d}',
            'aula':         p.aula or '',
            'numero_serie': p.numero_serie or '',
            'marca':        p.marca or '',
            'modelo':       p.modelo or '',
            'estado':       p.estado,
        })
    return jsonify(resultado)


# ── Impresoras 3D ─────────────────────────────────────────────────────────────

@etiquetas_bp.route('/impresoras')
@login_required
def impresoras():
    return render_template('etiquetas/impresoras.html')


@etiquetas_bp.route('/api/impresoras')
@login_required
def api_impresoras():
    imps = Impresora3D.query.filter(
        Impresora3D.estado != 'baja'
    ).order_by(Impresora3D.numero_interno).all()
    resultado = []
    for imp in imps:
        resultado.append({
            'id':             imp.id,
            'codigo':         f'IMP-{imp.numero_interno}',
            'numero_interno': imp.numero_interno or '',
            'numero_serie':   imp.numero_serie or '',
            'modelo':         imp.modelo or '',
            'aula':           imp.aula or '',
            'estado':         imp.estado,
        })
    return jsonify(resultado)
