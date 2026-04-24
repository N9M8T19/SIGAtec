# routes/ubicaciones.py
"""
Módulo Ubicaciones de Equipos — registro fijo de dónde está cada TV,
Pantalla Digital e Impresora 3D en el establecimiento.

NO pisa AsignacionInterna (esa tabla es para netbooks fuera de carro).

Registrar en app.py:
    from routes.ubicaciones import ubicaciones_bp
    app.register_blueprint(ubicaciones_bp)
"""

from flask import (Blueprint, render_template, request, redirect,
                   url_for, flash, send_file)
from flask_login import login_required, current_user
from io import BytesIO

from models import db, TV, PantallaDigital, Impresora3D, UbicacionEquipo
from services.pdf_reportes import pdf_etiquetas_equipos

ubicaciones_bp = Blueprint('ubicaciones', __name__, url_prefix='/ubicaciones')

TIPOS = {
    'tv':               'TV',
    'pantalla_digital': 'Pantalla Digital',
    'impresora_3d':     'Impresora 3D',
}


def _get_equipo(tipo, equipo_id):
    """Devuelve el objeto del equipo correspondiente al tipo."""
    if tipo == 'tv':
        return TV.query.get(equipo_id)
    if tipo == 'pantalla_digital':
        return PantallaDigital.query.get(equipo_id)
    if tipo == 'impresora_3d':
        return Impresora3D.query.get(equipo_id)
    return None


def _label_equipo(tipo, obj):
    """Etiqueta legible para mostrar en tablas."""
    if obj is None:
        return '—'
    if tipo == 'tv':
        return f'{obj.codigo} — {obj.marca} {obj.modelo}'
    if tipo == 'pantalla_digital':
        return getattr(obj, 'nombre', f'Pantalla #{obj.id}')
    if tipo == 'impresora_3d':
        num = getattr(obj, 'numero_interno', obj.id)
        return f'IMP-{num:02d} — {getattr(obj,"marca","")} {getattr(obj,"modelo","")}'
    return str(obj)


# ── Listado ────────────────────────────────────────────────────────────────────

@ubicaciones_bp.route('/')
@login_required
def index():
    filtro = request.args.get('tipo', '')
    q = UbicacionEquipo.query.filter_by(activa=True)
    if filtro:
        q = q.filter_by(tipo_equipo=filtro)
    ubics = q.order_by(UbicacionEquipo.aula).all()

    items = []
    for u in ubics:
        obj = _get_equipo(u.tipo_equipo, u.equipo_id)
        items.append({
            'ubic':        u,
            'label_equipo': _label_equipo(u.tipo_equipo, obj),
            'tipo_label':   TIPOS.get(u.tipo_equipo, u.tipo_equipo),
        })

    return render_template('ubicaciones/index.html',
                           items=items, tipos=TIPOS, filtro=filtro)


# ── Nueva ──────────────────────────────────────────────────────────────────────

@ubicaciones_bp.route('/nueva', methods=['GET', 'POST'])
@login_required
def nueva():
    if current_user.rol not in ('Administrador', 'Directivo'):
        flash('No tenés permiso para registrar ubicaciones.', 'danger')
        return redirect(url_for('ubicaciones.index'))

    tvs        = TV.query.filter(TV.estado != 'de_baja').order_by(TV.numero_interno).all()
    pantallas  = PantallaDigital.query.order_by(PantallaDigital.id).all()
    impresoras = Impresora3D.query.order_by(Impresora3D.id).all()

    if request.method == 'POST':
        f    = request.form
        tipo = f['tipo_equipo']
        eid  = int(f['equipo_id'])

        # desactivar ubicación previa del mismo equipo si existe
        prev = UbicacionEquipo.query.filter_by(
            tipo_equipo=tipo, equipo_id=eid, activa=True).first()
        if prev:
            prev.activa = False

        ubic = UbicacionEquipo(
            tipo_equipo       = tipo,
            equipo_id         = eid,
            aula              = f['aula'].strip(),
            sector            = f.get('sector', '').strip() or None,
            piso              = f.get('piso', '').strip() or None,
            descripcion       = f.get('descripcion', '').strip() or None,
            registrado_por_id = current_user.id,
        )

        # actualizar campo aula en el modelo TV directamente
        if tipo == 'tv':
            tv = TV.query.get(eid)
            if tv:
                tv.aula = f['aula'].strip()

        db.session.add(ubic)
        db.session.commit()
        flash('Ubicación registrada correctamente.', 'success')
        return redirect(url_for('ubicaciones.index'))

    return render_template('ubicaciones/form.html',
                           tvs=tvs, pantallas=pantallas, impresoras=impresoras)


# ── Desactivar ─────────────────────────────────────────────────────────────────

@ubicaciones_bp.route('/<int:ubic_id>/desactivar', methods=['POST'])
@login_required
def desactivar(ubic_id):
    if current_user.rol not in ('Administrador', 'Directivo'):
        flash('No tenés permiso.', 'danger')
        return redirect(url_for('ubicaciones.index'))
    ubic = UbicacionEquipo.query.get_or_404(ubic_id)
    ubic.activa = False
    db.session.commit()
    flash('Ubicación eliminada.', 'secondary')
    return redirect(url_for('ubicaciones.index'))


# ── PDF Etiquetas ──────────────────────────────────────────────────────────────

@ubicaciones_bp.route('/etiquetas')
@login_required
def etiquetas():
    """
    PDF con etiquetas para todos los equipos con ubicación activa.
    Parámetro ?tipo=tv|pantalla_digital|impresora_3d para filtrar.
    """
    tipo_filtro = request.args.get('tipo', '')

    tvs_data        = []
    pantallas_data  = []
    impresoras_data = []

    if not tipo_filtro or tipo_filtro == 'tv':
        for u in UbicacionEquipo.query.filter_by(tipo_equipo='tv', activa=True).all():
            tv = TV.query.get(u.equipo_id)
            if tv:
                tvs_data.append({'equipo': tv, 'ubic': u})

    if not tipo_filtro or tipo_filtro == 'pantalla_digital':
        for u in UbicacionEquipo.query.filter_by(tipo_equipo='pantalla_digital', activa=True).all():
            p = PantallaDigital.query.get(u.equipo_id)
            if p:
                pantallas_data.append({'equipo': p, 'ubic': u})

    if not tipo_filtro or tipo_filtro == 'impresora_3d':
        for u in UbicacionEquipo.query.filter_by(tipo_equipo='impresora_3d', activa=True).all():
            imp = Impresora3D.query.get(u.equipo_id)
            if imp:
                impresoras_data.append({'equipo': imp, 'ubic': u})

    buf = pdf_etiquetas_equipos(tvs_data, pantallas_data, impresoras_data)
    nombre = f'etiquetas_{tipo_filtro or "equipos"}.pdf'
    return send_file(BytesIO(buf), mimetype='application/pdf',
                     download_name=nombre, as_attachment=True)
