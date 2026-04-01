"""
routes/stock.py
Control de stock de netbooks por carro.
Compara el inventario físico (escaneado) contra el sistema.
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_required, current_user
from models import db, Carro, Netbook
from datetime import datetime

stock_bp = Blueprint('stock', __name__, url_prefix='/stock')


@stock_bp.route('/')
@login_required
def index():
    carros = Carro.query.filter(Carro.estado != 'baja').order_by(Carro.numero_fisico).all()
    return render_template('stock/index.html', carros=carros)


@stock_bp.route('/relevar/<int:carro_id>', methods=['GET', 'POST'])
@login_required
def relevar(carro_id):
    """Pantalla de escaneo/ingreso de series para un carro."""
    carro = Carro.query.get_or_404(carro_id)

    if request.method == 'POST':
        # Recibir las series escaneadas
        series_raw = request.form.get('series_escaneadas', '')
        series_lista = [s.strip().upper() for s in series_raw.splitlines() if s.strip()]

        if not series_lista:
            flash('No ingresaste ningún número de serie.', 'danger')
            return redirect(url_for('stock.relevar', carro_id=carro_id))

        # Comparar contra el sistema
        series_sistema = {nb.numero_serie.upper(): nb
                          for nb in carro.netbooks
                          if nb.numero_serie}

        series_escaneadas_set = set(series_lista)
        series_sistema_set    = set(series_sistema.keys())

        # Presentes en el sistema y encontradas físicamente ✅
        encontradas = [series_sistema[s] for s in series_escaneadas_set & series_sistema_set]

        # En el sistema pero NO encontradas físicamente ❌ (faltan)
        faltantes = [series_sistema[s] for s in series_sistema_set - series_escaneadas_set]

        # Escaneadas pero NO están en el sistema ⚠️ (extras / no registradas)
        no_registradas = list(series_escaneadas_set - series_sistema_set)

        # Guardar resultado en session para el PDF
        session['stock_resultado'] = {
            'carro_id':         carro_id,
            'carro_display':    carro.display,
            'fecha':            datetime.now().strftime('%d/%m/%Y %H:%M'),
            'total_sistema':    len(series_sistema_set),
            'total_escaneadas': len(series_escaneadas_set),
            'encontradas':      len(encontradas),
            'faltantes': [{
                'numero_interno': nb.numero_interno or '—',
                'numero_serie':   nb.numero_serie or '—',
                'alumno':         nb.alumno or '—',
                'estado':         nb.estado
            } for nb in faltantes],
            'no_registradas': no_registradas,
            'usuario':  current_user.nombre_completo,
        }

        return render_template('stock/resultado.html',
                               carro=carro,
                               encontradas=encontradas,
                               faltantes=faltantes,
                               no_registradas=no_registradas,
                               fecha=datetime.now().strftime('%d/%m/%Y %H:%M'),
                               usuario=current_user.nombre_completo)

    return render_template('stock/relevar.html', carro=carro)


@stock_bp.route('/pdf/<int:carro_id>')
@login_required
def pdf(carro_id):
    """Genera el PDF del último resultado de stock."""
    resultado = session.get('stock_resultado')

    if not resultado or resultado.get('carro_id') != carro_id:
        flash('No hay resultado de stock disponible. Realizá el relevamiento primero.', 'warning')
        return redirect(url_for('stock.relevar', carro_id=carro_id))

    from services.pdf_stock import pdf_control_stock
    carro = Carro.query.get_or_404(carro_id)
    return pdf_control_stock(carro, resultado)
