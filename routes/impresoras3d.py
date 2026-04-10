# routes/impresoras3d.py
# ─────────────────────────────────────────────────────────────────────────────
# Módulo: Inventario → Impresoras 3D
# CRUD completo con estados (operativa / en servicio / baja)
# ─────────────────────────────────────────────────────────────────────────────

from flask import (Blueprint, render_template, request,
                   redirect, url_for, flash)
from flask_login import login_required, current_user
from models import db, Impresora3D

impresoras3d_bp = Blueprint('impresoras3d', __name__,
                             url_prefix='/impresoras3d')

# ── Helpers ──────────────────────────────────────────────────────────────────

ESTADOS = {
    'operativa':   ('Operativa',       'success'),
    'en_servicio': ('En servicio téc.','warning'),
    'baja':        ('Baja',            'danger'),
}

def _solo_admin_directivo():
    return current_user.rol in ('Administrador', 'Directivo')


# ── Listado ───────────────────────────────────────────────────────────────────

@impresoras3d_bp.route('/')
@login_required
def index():
    q       = request.args.get('q', '').strip()
    estado  = request.args.get('estado', '')

    query = Impresora3D.query

    if q:
        like = f'%{q}%'
        query = query.filter(
            db.or_(
                Impresora3D.numero_interno.ilike(like),
                Impresora3D.numero_serie.ilike(like),
                Impresora3D.modelo.ilike(like),
                Impresora3D.aula.ilike(like),
            )
        )

    if estado in ESTADOS:
        query = query.filter(Impresora3D.estado == estado)

    impresoras = query.order_by(Impresora3D.numero_interno).all()

    return render_template(
        'impresoras3d/index.html',
        impresoras=impresoras,
        estados=ESTADOS,
        q=q,
        estado_filtro=estado,
    )


# ── Alta ──────────────────────────────────────────────────────────────────────

@impresoras3d_bp.route('/nueva', methods=['GET', 'POST'])
@login_required
def nueva():
    if not _solo_admin_directivo():
        flash('No tenés permisos para agregar impresoras.', 'danger')
        return redirect(url_for('impresoras3d.index'))

    if request.method == 'POST':
        numero_interno = request.form.get('numero_interno', '').strip()
        numero_serie   = request.form.get('numero_serie', '').strip()
        modelo         = request.form.get('modelo', '').strip()
        aula           = request.form.get('aula', '').strip()
        observaciones  = request.form.get('observaciones', '').strip()

        # Validaciones básicas
        if not numero_interno or not modelo:
            flash('El número interno y el modelo son obligatorios.', 'danger')
            return render_template('impresoras3d/form.html',
                                   accion='Nueva', estados=ESTADOS)

        if Impresora3D.query.filter_by(numero_interno=numero_interno).first():
            flash(f'Ya existe una impresora con el número interno "{numero_interno}".', 'danger')
            return render_template('impresoras3d/form.html',
                                   accion='Nueva', estados=ESTADOS)

        imp = Impresora3D(
            numero_interno=numero_interno,
            numero_serie=numero_serie or None,
            modelo=modelo,
            aula=aula or None,
            observaciones=observaciones or None,
        )
        db.session.add(imp)
        db.session.commit()
        flash(f'Impresora 3D #{numero_interno} agregada correctamente.', 'success')
        return redirect(url_for('impresoras3d.index'))

    return render_template('impresoras3d/form.html',
                           accion='Nueva', imp=None, estados=ESTADOS)


# ── Editar ────────────────────────────────────────────────────────────────────

@impresoras3d_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    if not _solo_admin_directivo():
        flash('No tenés permisos para editar impresoras.', 'danger')
        return redirect(url_for('impresoras3d.index'))

    imp = Impresora3D.query.get_or_404(id)

    if request.method == 'POST':
        numero_interno = request.form.get('numero_interno', '').strip()
        numero_serie   = request.form.get('numero_serie', '').strip()
        modelo         = request.form.get('modelo', '').strip()
        aula           = request.form.get('aula', '').strip()
        estado         = request.form.get('estado', 'operativa')
        observaciones  = request.form.get('observaciones', '').strip()

        if not numero_interno or not modelo:
            flash('El número interno y el modelo son obligatorios.', 'danger')
            return render_template('impresoras3d/form.html',
                                   accion='Editar', imp=imp, estados=ESTADOS)

        # Verificar duplicado (excluyendo la impresora actual)
        existente = Impresora3D.query.filter(
            Impresora3D.numero_interno == numero_interno,
            Impresora3D.id != id
        ).first()
        if existente:
            flash(f'Ya existe otra impresora con el número interno "{numero_interno}".', 'danger')
            return render_template('impresoras3d/form.html',
                                   accion='Editar', imp=imp, estados=ESTADOS)

        imp.numero_interno = numero_interno
        imp.numero_serie   = numero_serie or None
        imp.modelo         = modelo
        imp.aula           = aula or None
        imp.estado         = estado if estado in ESTADOS else 'operativa'
        imp.observaciones  = observaciones or None

        db.session.commit()
        flash(f'Impresora 3D #{numero_interno} actualizada.', 'success')
        return redirect(url_for('impresoras3d.index'))

    return render_template('impresoras3d/form.html',
                           accion='Editar', imp=imp, estados=ESTADOS)


# ── Eliminar ──────────────────────────────────────────────────────────────────

@impresoras3d_bp.route('/<int:id>/eliminar', methods=['POST'])
@login_required
def eliminar(id):
    if not _solo_admin_directivo():
        flash('No tenés permisos para eliminar impresoras.', 'danger')
        return redirect(url_for('impresoras3d.index'))

    imp = Impresora3D.query.get_or_404(id)
    num = imp.numero_interno
    db.session.delete(imp)
    db.session.commit()
    flash(f'Impresora 3D #{num} eliminada.', 'success')
    return redirect(url_for('impresoras3d.index'))
