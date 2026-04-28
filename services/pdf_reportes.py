"""
services/pdf_reportes.py
Generación de PDFs para SIGA-Tec usando ReportLab.
"""

import os
from io import BytesIO
from datetime import datetime, timedelta

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, Image
)
from flask import send_file

# Conversión UTC → Argentina (UTC-3)
ARG_OFFSET = timedelta(hours=-3)

def _arg(dt):
    """Convierte UTC a hora Argentina (UTC-3)."""
    if dt is None:
        return '—'
    return (dt + ARG_OFFSET).strftime('%d/%m %H:%M')

def _arg_full(dt):
    """Convierte UTC a hora Argentina (UTC-3)."""
    if dt is None:
        return '—'
    return (dt + ARG_OFFSET).strftime('%d/%m/%Y %H:%M')

AZUL_ESCUELA = colors.HexColor('#1e3a8a')
AZUL_CLARO   = colors.HexColor('#dbeafe')
GRIS_CLARO   = colors.HexColor('#f3f4f6')
NARANJA      = colors.HexColor('#f97316')
ROJO         = colors.HexColor('#dc2626')
VERDE        = colors.HexColor('#16a34a')

styles = getSampleStyleSheet()

STYLE_TITULO = ParagraphStyle('Titulo', parent=styles['Normal'],
    fontSize=16, fontName='Helvetica-Bold',
    textColor=AZUL_ESCUELA, alignment=TA_CENTER, spaceAfter=4)
STYLE_SUBTITULO = ParagraphStyle('Subtitulo', parent=styles['Normal'],
    fontSize=10, fontName='Helvetica',
    textColor=colors.grey, alignment=TA_CENTER, spaceAfter=2)
STYLE_SECCION = ParagraphStyle('Seccion', parent=styles['Normal'],
    fontSize=12, fontName='Helvetica-Bold',
    textColor=AZUL_ESCUELA, spaceBefore=10, spaceAfter=4)
STYLE_NORMAL = ParagraphStyle('Normal2', parent=styles['Normal'],
    fontSize=9, fontName='Helvetica')
STYLE_FECHA = ParagraphStyle('Fecha', parent=styles['Normal'],
    fontSize=8, fontName='Helvetica',
    textColor=colors.grey, alignment=TA_RIGHT)
STYLE_CAMPO = ParagraphStyle('Campo', parent=styles['Normal'],
    fontSize=9, fontName='Helvetica-Bold', textColor=AZUL_ESCUELA)


def _encabezado(story, titulo, subtitulo=''):
    logo_path = os.path.join('static', 'img', 'logo_escuela.png')
    fecha_str = (datetime.utcnow() + ARG_OFFSET).strftime('%d/%m/%Y %H:%M')

    logo_cell = ''
    if os.path.exists(logo_path):
        try:
            logo_cell = Image(logo_path, width=2*cm, height=2*cm)
        except Exception:
            logo_cell = ''

    titulo_cell = [
        Paragraph('E.T. N°7 D.E. 5 — Dolores Lavalle de Lavalle', STYLE_SUBTITULO),
        Paragraph('Sistema Integral de Recursos Tecnológicos', STYLE_SUBTITULO),
        Paragraph(titulo, STYLE_TITULO),
    ]
    if subtitulo:
        titulo_cell.append(Paragraph(subtitulo, STYLE_SUBTITULO))

    fecha_cell = Paragraph(f'Generado:\n{fecha_str}', STYLE_FECHA)

    tabla_header = Table([[logo_cell, titulo_cell, fecha_cell]],
                         colWidths=[2.5*cm, 13*cm, 3*cm])
    tabla_header.setStyle(TableStyle([
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN',         (0, 0), (0, 0),   'CENTER'),
        ('ALIGN',         (2, 0), (2, 0),   'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(tabla_header)
    story.append(HRFlowable(width='100%', thickness=2, color=AZUL_ESCUELA))
    story.append(Spacer(1, 0.3*cm))


def _tabla_estilo(header_color=None):
    if header_color is None:
        header_color = AZUL_ESCUELA
    return TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0),  header_color),
        ('TEXTCOLOR',     (0, 0), (-1, 0),  colors.white),
        ('FONTNAME',      (0, 0), (-1, 0),  'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, 0),  9),
        ('ALIGN',         (0, 0), (-1, 0),  'CENTER'),
        ('FONTNAME',      (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE',      (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS',(0, 1), (-1, -1), [colors.white, GRIS_CLARO]),
        ('GRID',          (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING',    (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING',   (0, 0), (-1, -1), 6),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 6),
    ])


def _generar_response(buffer, nombre_archivo):
    buffer.seek(0)
    return send_file(buffer, as_attachment=True,
                     download_name=nombre_archivo, mimetype='application/pdf')


def _campo_firma(label, ancho=8*cm):
    """Genera una celda con línea para completar a mano."""
    return [Paragraph(label, STYLE_CAMPO),
            HRFlowable(width=ancho, thickness=0.5, color=colors.grey),
            Spacer(1, 0.1*cm)]


# ─────────────────────────────────────────────────────────────────────────────
#  1. LISTADO DE NETBOOKS POR CARRO
# ─────────────────────────────────────────────────────────────────────────────

def pdf_netbooks_por_carro(carro):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                             rightMargin=1.5*cm, leftMargin=1.5*cm,
                             topMargin=1.5*cm, bottomMargin=1.5*cm)
    story = []
    _encabezado(story, f'Inventario de Netbooks — Carro {carro.display}',
                f'División: {carro.division or "—"} | Aula: {carro.aula or "—"}')

    stats_data = [['Total', 'Operativas', 'Servicio Técnico'],
                  [str(carro.total_netbooks), str(carro.operativas), str(carro.en_servicio)]]
    t = Table(stats_data, colWidths=[5*cm, 5*cm, 5*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0),  AZUL_CLARO),
        ('TEXTCOLOR',     (0, 0), (-1, 0),  AZUL_ESCUELA),
        ('FONTNAME',      (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, -1), 10),
        ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
        ('GRID',          (0, 0), (-1, -1), 0.5, colors.HexColor('#93c5fd')),
        ('TOPPADDING',    (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.4*cm))

    data = [['N° Interno', 'N° Serie', 'Alumno Asignado', 'Estado']]
    for nb in carro.netbooks:
        estado = 'Operativa' if nb.estado == 'operativa' else 'Servicio Técnico'
        data.append([nb.numero_interno or '—', nb.numero_serie or 'Sin serie',
                     nb.alumno or '—', estado])

    if len(data) > 1:
        t2 = Table(data, colWidths=[3*cm, 5*cm, 6*cm, 4*cm])
        estilo = _tabla_estilo()
        for i, nb in enumerate(carro.netbooks, start=1):
            if nb.estado == 'servicio_tecnico':
                estilo.add('TEXTCOLOR', (3, i), (3, i), NARANJA)
                estilo.add('FONTNAME',  (3, i), (3, i), 'Helvetica-Bold')
        t2.setStyle(estilo)
        story.append(t2)
    else:
        story.append(Paragraph('No hay netbooks en este carro.', STYLE_NORMAL))

    doc.build(story)
    return _generar_response(buffer, f'netbooks_carro_{carro.numero_fisico}.pdf')


# ─────────────────────────────────────────────────────────────────────────────
#  2. LISTADO DE TODOS LOS CARROS
# ─────────────────────────────────────────────────────────────────────────────

def pdf_listado_carros(carros):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                             rightMargin=1.5*cm, leftMargin=1.5*cm,
                             topMargin=1.5*cm, bottomMargin=1.5*cm)
    story = []
    _encabezado(story, 'Listado General de Carros')

    data = [['Carro', 'División', 'Aula', 'Total NB', 'Operativas', 'Servicio', 'Estado']]
    for c in carros:
        data.append([c.display, c.division or '—', c.aula or '—',
                     str(c.total_netbooks), str(c.operativas),
                     str(c.en_servicio), c.estado.capitalize()])

    t = Table(data, colWidths=[2.5*cm, 3.5*cm, 2.5*cm, 2*cm, 2.5*cm, 2.5*cm, 2.5*cm])
    t.setStyle(_tabla_estilo())
    story.append(t)
    doc.build(story)
    return _generar_response(buffer, 'listado_carros.pdf')


# ─────────────────────────────────────────────────────────────────────────────
#  3. NETBOOKS ASIGNADAS A ALUMNOS
# ─────────────────────────────────────────────────────────────────────────────

def pdf_netbooks_asignadas(carro=None):
    from models import Netbook
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                             rightMargin=1.5*cm, leftMargin=1.5*cm,
                             topMargin=1.5*cm, bottomMargin=1.5*cm)
    story = []
    titulo = f'Netbooks Asignadas — Carro {carro.display}' if carro else 'Netbooks Asignadas a Alumnos'
    _encabezado(story, titulo)

    if carro:
        netbooks = [nb for nb in carro.netbooks if nb.alumno]
    else:
        netbooks = Netbook.query.filter(Netbook.alumno != None, Netbook.alumno != '').all()

    data = [['Carro', 'N° Interno', 'N° Serie', 'Alumno Asignado', 'Estado']]
    for nb in netbooks:
        data.append([nb.carro.display if nb.carro else '—',
                     nb.numero_interno or '—', nb.numero_serie or '—',
                     nb.alumno or '—',
                     'Operativa' if nb.estado == 'operativa' else 'Servicio'])

    if len(data) > 1:
        t = Table(data, colWidths=[2.5*cm, 2.5*cm, 4.5*cm, 6*cm, 3*cm])
        t.setStyle(_tabla_estilo())
        story.append(t)
        story.append(Spacer(1, 0.3*cm))
        story.append(Paragraph(f'Total: {len(data)-1} netbook(s) asignada(s)', STYLE_NORMAL))
    else:
        story.append(Paragraph('No hay netbooks con alumno asignado.', STYLE_NORMAL))

    doc.build(story)
    nombre = f'asignadas_carro_{carro.numero_fisico}.pdf' if carro else 'netbooks_asignadas.pdf'
    return _generar_response(buffer, nombre)


# ─────────────────────────────────────────────────────────────────────────────
#  4. SERVICIO TÉCNICO CON CAMPO DE NÚMERO DE RECLAMO
# ─────────────────────────────────────────────────────────────────────────────

def pdf_servicio_tecnico():
    from models import Netbook, Carro
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                             rightMargin=1.5*cm, leftMargin=1.5*cm,
                             topMargin=1.5*cm, bottomMargin=1.5*cm)
    story = []
    _encabezado(story, 'Reporte de Servicio Técnico')

    # ── SECCIÓN 1: CARROS FÍSICOS EN SERVICIO ────────────────────
    carros_servicio = Carro.query.filter_by(estado='en_servicio').order_by(Carro.numero_fisico).all()

    story.append(Paragraph('CARROS FÍSICOS EN SERVICIO TÉCNICO', STYLE_SUBTITULO))
    story.append(Spacer(1, 0.2*cm))

    if carros_servicio:
        data_carros = [['Carro', 'Aula', 'División', 'Motivo', 'Netbooks']]
        for c in carros_servicio:
            data_carros.append([
                c.display,
                c.aula or '—',
                c.division or '—',
                Paragraph(c.motivo_servicio or '—', STYLE_NORMAL),
                str(c.total_netbooks),
            ])
        t = Table(data_carros, colWidths=[2.5*cm, 2.5*cm, 3*cm, 7*cm, 2.5*cm])
        t.setStyle(_tabla_estilo(NARANJA))
        story.append(t)
        story.append(Spacer(1, 0.3*cm))
        story.append(Paragraph(f'Total: {len(carros_servicio)} carro(s) en servicio.', STYLE_NORMAL))
    else:
        story.append(Paragraph('No hay carros físicos en servicio técnico.', STYLE_NORMAL))

    story.append(Spacer(1, 0.8*cm))

    # ── SECCIÓN 2: NETBOOKS EN SERVICIO ──────────────────────────
    netbooks = Netbook.query.filter_by(estado='servicio_tecnico').all()

    story.append(Paragraph('NETBOOKS EN SERVICIO TÉCNICO', STYLE_SUBTITULO))
    story.append(Spacer(1, 0.2*cm))

    if netbooks:
        data_nb = [['Carro', 'Aula', 'N° Interno', 'N° Serie', 'Problema']]
        for nb in netbooks:
            data_nb.append([
                nb.carro.display if nb.carro else '—',
                nb.carro.aula if nb.carro else '—',
                nb.numero_interno or '—',
                nb.numero_serie or '—',
                Paragraph(nb.problema or '—', STYLE_NORMAL),
            ])
        t = Table(data_nb, colWidths=[2.5*cm, 2.5*cm, 2.5*cm, 5*cm, 6*cm])
        t.setStyle(_tabla_estilo(NARANJA))
        story.append(t)
        story.append(Spacer(1, 0.3*cm))
        story.append(Paragraph(f'Total: {len(netbooks)} netbook(s) en servicio.', STYLE_NORMAL))
    else:
        story.append(Paragraph('No hay netbooks en servicio técnico.', STYLE_NORMAL))

    # Firma
    story.append(Spacer(1, 1*cm))
    firma_data = [[
        Paragraph('_________________________\nEncargado/a', STYLE_NORMAL),
        Paragraph('_________________________\nDirectivo/a', STYLE_NORMAL),
        Paragraph('_________________________\nFecha', STYLE_NORMAL),
    ]]
    t_firma = Table(firma_data, colWidths=[5.5*cm, 5.5*cm, 5.5*cm])
    t_firma.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER')]))
    story.append(t_firma)

    doc.build(story)
    return _generar_response(buffer, 'servicio_tecnico.pdf')


def pdf_transferencia(netbooks_transferidas, carro_origen, carro_destino, usuario):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                             rightMargin=1.5*cm, leftMargin=1.5*cm,
                             topMargin=1.5*cm, bottomMargin=1.5*cm)
    story = []
    _encabezado(story, 'Informe de Transferencia de Netbooks')

    # Info de la transferencia
    info_data = [
        ['Carro Origen', 'Carro Destino', 'Cantidad', 'Fecha', 'Autorizado por'],
        [carro_origen.display, carro_destino.display,
         str(len(netbooks_transferidas)),
         (datetime.utcnow() + ARG_OFFSET).strftime('%d/%m/%Y %H:%M'), usuario]
    ]
    t_info = Table(info_data, colWidths=[3*cm, 3*cm, 2.5*cm, 4*cm, 6*cm])
    t_info.setStyle(_tabla_estilo(VERDE))
    story.append(t_info)
    story.append(Spacer(1, 0.5*cm))

    # Detalle de netbooks transferidas
    story.append(Paragraph('Detalle de Netbooks Transferidas', STYLE_SECCION))
    data = [['N° Interno', 'N° Serie', 'Alumno Asignado']]
    for nb in netbooks_transferidas:
        data.append([nb.numero_interno or '—', nb.numero_serie or '—', nb.alumno or '—'])

    t = Table(data, colWidths=[3.5*cm, 7*cm, 8*cm])
    t.setStyle(_tabla_estilo())
    story.append(t)

    # Firma
    story.append(Spacer(1, 1.5*cm))
    firma_data = [[
        Paragraph('_________________________\nEncargado/a que transfiere', STYLE_NORMAL),
        Paragraph('_________________________\nEncargado/a que recibe', STYLE_NORMAL),
        Paragraph('_________________________\nFecha y hora', STYLE_NORMAL),
    ]]
    t_firma = Table(firma_data, colWidths=[5.5*cm, 5.5*cm, 5.5*cm])
    t_firma.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER')]))
    story.append(t_firma)

    doc.build(story)
    return _generar_response(buffer, f'transferencia_{carro_origen.numero_fisico}_a_{carro_destino.numero_fisico}.pdf')


# ─────────────────────────────────────────────────────────────────────────────
#  6. HISTORIAL DE PRÉSTAMOS DE CARROS
# ─────────────────────────────────────────────────────────────────────────────

def pdf_historial_carros(prestamos, periodo='todos'):
    from reportlab.lib.pagesizes import landscape
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4),
                             rightMargin=1.5*cm, leftMargin=1.5*cm,
                             topMargin=1.5*cm, bottomMargin=1.5*cm)
    story = []
    _encabezado(story, 'Historial de Préstamos — Carros',
                f'Período: {periodo.capitalize()}')

    STYLE_CELL = ParagraphStyle('Cell', parent=styles['Normal'],
        fontSize=8, fontName='Helvetica')

    # 9 columnas — ancho útil landscape A4 ≈ 25.7 cm
    data = [['Código', 'Docente', 'Carro', 'Retiro', 'Devolución', 'Duración',
             'Autorizó Retiro', 'Autorizó Devolución', 'Estado']]
    for p in prestamos:
        dur = '—'
        if p.duracion_minutos:
            dur = f'{p.duracion_minutos//60}h {p.duracion_minutos%60}m'
        elif p.hora_devolucion and p.hora_retiro:
            diff = int((p.hora_devolucion - p.hora_retiro).total_seconds() // 60)
            dur = f'{diff//60}h {diff%60}m'
        nombre_docente = ''
        if p.docente:
            nombre_docente = (f'{p.docente.apellido}, {p.docente.nombre}'
                              if hasattr(p.docente, 'apellido')
                              else (p.docente.nombre_completo
                                    if hasattr(p.docente, 'nombre_completo')
                                    else str(p.docente)))
        data.append([
            p.codigo or '—',
            Paragraph(nombre_docente, STYLE_CELL),
            p.carro.display if p.carro else '—',
            _arg(p.hora_retiro),
            _arg(p.hora_devolucion) if p.hora_devolucion else '—',
            dur,
            Paragraph(p.encargado_retiro    or '—', STYLE_CELL),
            Paragraph(p.encargado_devolucion or '—', STYLE_CELL),
            'Activo' if p.estado == 'activo' else 'Devuelto',
        ])

    if len(data) > 1:
        # suma colWidths = 25.7 cm
        t = Table(data, colWidths=[1.5*cm, 5.0*cm, 2.2*cm, 2.7*cm, 2.7*cm,
                                    1.8*cm, 4.5*cm, 4.5*cm, 1.8*cm])
        estilo = _tabla_estilo()
        for i, p in enumerate(prestamos, start=1):
            if p.estado == 'activo':
                estilo.add('TEXTCOLOR', (8, i), (8, i), NARANJA)
                estilo.add('FONTNAME',  (8, i), (8, i), 'Helvetica-Bold')
        t.setStyle(estilo)
        story.append(t)
        story.append(Spacer(1, 0.3*cm))
        story.append(Paragraph(f'Total: {len(data)-1} préstamo(s)', STYLE_NORMAL))
    else:
        story.append(Paragraph('No hay préstamos para este período.', STYLE_NORMAL))

    doc.build(story)
    return _generar_response(buffer, f'historial_carros_{periodo}.pdf')


# ─────────────────────────────────────────────────────────────────────────────
#  7. HISTORIAL ESPACIO DIGITAL
# ─────────────────────────────────────────────────────────────────────────────

def pdf_historial_netbooks(prestamos, periodo='todos'):
    from reportlab.lib.pagesizes import landscape
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4),
                             rightMargin=1.5*cm, leftMargin=1.5*cm,
                             topMargin=1.5*cm, bottomMargin=1.5*cm)
    story = []
    _encabezado(story, 'Historial de Préstamos — Espacio Digital',
                f'Período: {periodo.capitalize()}')

    STYLE_DETALLE = ParagraphStyle('Detalle', parent=styles['Normal'],
        fontSize=7, fontName='Helvetica', textColor=colors.HexColor('#374151'))
    STYLE_NB = ParagraphStyle('NB', parent=styles['Normal'],
        fontSize=7, fontName='Helvetica-Bold', textColor=AZUL_ESCUELA)
    STYLE_CELL = ParagraphStyle('Cell', parent=styles['Normal'],
        fontSize=8, fontName='Helvetica')

    # 9 columnas — ancho útil landscape A4 ≈ 25.7 cm
    data = [['Código', 'Docente', 'Carro(s)', 'Netbooks', 'Retiro', 'Devolución',
             'Autorizó Retiro', 'Autorizó Devolución', 'Estado']]
    row_estados = []

    for p in prestamos:
        nombre_docente = ''
        if p.docente:
            nombre_docente = (f'{p.docente.apellido}, {p.docente.nombre}'
                              if hasattr(p.docente, 'apellido')
                              else str(p.docente))

        # Carro(s): buscar via netbook_id (PrestamoNetbookItem no tiene relationship definida)
        from models import Netbook
        carros_vistos = {}
        if p.items:
            for item in p.items:
                if item.netbook_id:
                    nb = Netbook.query.get(item.netbook_id)
                    if nb and nb.carro and nb.carro.id not in carros_vistos:
                        carros_vistos[nb.carro.id] = nb.carro.display
        carro_cell = Paragraph('\n'.join(carros_vistos.values()) if carros_vistos else '—',
                                STYLE_CELL)

        # Netbooks: "N°12 — Alumno" por línea
        if p.items:
            lineas = [f'N°{i.numero_interno}' + (f' — {i.alumno}' if i.alumno else '')
                      for i in p.items]
            nb_cell = Paragraph('\n'.join(lineas), STYLE_NB)
        else:
            nb_cell = Paragraph('—', STYLE_DETALLE)

        data.append([
            p.codigo or '—',
            Paragraph(nombre_docente, STYLE_CELL),
            carro_cell,
            nb_cell,
            _arg(p.hora_retiro),
            _arg(p.hora_devolucion) if p.hora_devolucion else '—',
            Paragraph(p.encargado_retiro    or '—', STYLE_CELL),
            Paragraph(p.encargado_devolucion or '—', STYLE_CELL),
            'Activo' if p.estado == 'activo' else 'Devuelto',
        ])
        row_estados.append(p.estado)

    if len(data) > 1:
        # suma colWidths = 25.7 cm
        t = Table(data, colWidths=[1.5*cm, 4.2*cm, 2.3*cm, 4.0*cm,
                                    2.5*cm, 2.5*cm, 4.0*cm, 3.9*cm, 1.8*cm])
        estilo = _tabla_estilo(colors.HexColor('#1d4ed8'))
        estilo.add('ALIGN', (3, 0), (3, -1), 'LEFT')
        for i, estado in enumerate(row_estados, start=1):
            if estado == 'activo':
                estilo.add('TEXTCOLOR', (8, i), (8, i), NARANJA)
                estilo.add('FONTNAME',  (8, i), (8, i), 'Helvetica-Bold')
        t.setStyle(estilo)
        story.append(t)
        story.append(Spacer(1, 0.3*cm))
        story.append(Paragraph(f'Total: {len(data)-1} préstamo(s)', STYLE_NORMAL))
    else:
        story.append(Paragraph('No hay préstamos para este período.', STYLE_NORMAL))

    doc.build(story)
    return _generar_response(buffer, f'historial_espacio_digital_{periodo}.pdf')


# ─────────────────────────────────────────────────────────────────────────────
#  8. ESTADÍSTICAS
# ─────────────────────────────────────────────────────────────────────────────

def pdf_estadisticas(top_docentes, top_materias):
    """
    top_docentes: lista de (docente, total_prestamos)
    top_materias: lista de (materia_prestamo, total) — materia específica del módulo
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                             rightMargin=1.5*cm, leftMargin=1.5*cm,
                             topMargin=1.5*cm, bottomMargin=1.5*cm)
    story = []
    _encabezado(story, 'Estadísticas de Uso del Sistema')

    # ── Top Docentes ──────────────────────────────────────────────────────────
    story.append(Paragraph('Top Docentes por Préstamos', STYLE_SECCION))
    data = [['#', 'Docente', 'Total Préstamos']]
    for i, (docente, total) in enumerate(top_docentes, start=1):
        data.append([str(i), docente.nombre_completo, str(total)])

    if len(data) > 1:
        t = Table(data, colWidths=[1*cm, 13*cm, 3.5*cm])
        t.setStyle(_tabla_estilo())
        story.append(t)
    else:
        story.append(Paragraph('Sin datos.', STYLE_NORMAL))

    story.append(Spacer(1, 0.5*cm))

    # ── Top Materias ──────────────────────────────────────────────────────────
    story.append(Paragraph('Top Materias por Préstamos', STYLE_SECCION))
    data2 = [['#', 'Materia', 'Total Préstamos']]
    for i, (materia, total) in enumerate(top_materias, start=1):
        data2.append([str(i), materia or 'Sin materia asignada', str(total)])

    if len(data2) > 1:
        t2 = Table(data2, colWidths=[1*cm, 13*cm, 3.5*cm])
        t2.setStyle(_tabla_estilo(VERDE))
        story.append(t2)
    else:
        story.append(Paragraph('Sin datos.', STYLE_NORMAL))

    doc.build(story)
    return _generar_response(buffer, 'estadisticas.pdf')


# ─────────────────────────────────────────────────────────────────────────────
#  PDF ASIGNACIONES — CARRO COMPLETO
# ─────────────────────────────────────────────────────────────────────────────

def generar_pdf_asignaciones_carro(carro):
    """
    PDF con asignaciones del carro.
    Página 1: Turno Mañana (netbooks asignadas + alumnos sin netbook)
    Página 2: Turno Tarde  (netbooks asignadas + alumnos sin netbook)

    El tamaño de fuente se ajusta dinámicamente para que todo entre en una A4.
    No se muestra la columna Curso (ya figura en el encabezado).
    """
    from reportlab.platypus import PageBreak
    from reportlab.lib.pagesizes import A4
    from models import Alumno

    # ── Constantes de layout ─────────────────────────────────────────────────
    PAGE_W, PAGE_H = A4
    MARGIN        = 1.5 * cm
    USABLE_H      = PAGE_H - 2 * MARGIN   # altura útil total (~26.7cm en A4)

    # Overhead medido empíricamente:
    #   encabezado (logo+textos+HR+spacer): ~2.8cm
    #   stats tabla (2 filas con padding):  ~1.0cm
    #   spacer antes de tabla:              ~0.4cm
    OVERHEAD_BASE  = 4.2 * cm
    OVERHEAD_SINM  = 0.9 * cm   # título rojo "sin netbook" + spacer

    # Rangos de fuente permitidos
    FS_MIN, FS_MAX = 8, 14

    def _calcular_fs(n_filas_asig, n_filas_sin):
        """Devuelve el fontSize que hace entrar todo en la página."""
        for fs in range(FS_MAX, FS_MIN - 1, -1):
            row_h    = fs * 2.2          # alto de fila ≈ 2.2× la fuente (padding incluido)
            header_h = fs * 2.6          # fila de encabezado un poco más alta
            overhead = OVERHEAD_BASE
            if n_filas_sin:
                overhead += OVERHEAD_SINM
            total = (overhead
                     + header_h + n_filas_asig * row_h
                     + (header_h + n_filas_sin * row_h if n_filas_sin else 0))
            if total <= USABLE_H:
                return fs
        return FS_MIN   # si no entra ni con el mínimo, Platypus pagina automáticamente

    def _estilo_asig(fs):
        """TableStyle para la tabla de asignaciones con fuente dinámica."""
        padding = max(3, int(fs * 0.55))
        return TableStyle([
            ('BACKGROUND',    (0, 0), (-1, 0),  AZUL_ESCUELA),
            ('TEXTCOLOR',     (0, 0), (-1, 0),  colors.white),
            ('FONTNAME',      (0, 0), (-1, 0),  'Helvetica-Bold'),
            ('FONTSIZE',      (0, 0), (-1, 0),  fs),
            ('ALIGN',         (0, 0), (0, -1),  'CENTER'),   # col N° centrada
            ('ALIGN',         (1, 0), (1, -1),  'LEFT'),      # col Nombre izquierda
            ('FONTNAME',      (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE',      (0, 1), (-1, -1), fs),
            ('ROWBACKGROUNDS',(0, 1), (-1, -1), [colors.white, GRIS_CLARO]),
            ('GRID',          (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
            ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING',    (0, 0), (-1, -1), padding),
            ('BOTTOMPADDING', (0, 0), (-1, -1), padding),
            ('LEFTPADDING',   (0, 0), (-1, -1), 6),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 6),
        ])

    def _estilo_sin(fs):
        """TableStyle para la tabla de alumnos sin netbook (fondo rojo)."""
        padding = max(3, int(fs * 0.55))
        return TableStyle([
            ('BACKGROUND',    (0, 0), (-1, 0),  ROJO),
            ('TEXTCOLOR',     (0, 0), (-1, 0),  colors.white),
            ('FONTNAME',      (0, 0), (-1, 0),  'Helvetica-Bold'),
            ('FONTSIZE',      (0, 0), (-1, 0),  fs),
            ('ALIGN',         (0, 0), (-1, 0),  'CENTER'),
            ('FONTNAME',      (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE',      (0, 1), (-1, -1), fs),
            ('TEXTCOLOR',     (0, 1), (-1, -1), ROJO),
            ('ROWBACKGROUNDS',(0, 1), (-1, -1), [colors.HexColor('#fff1f2'),
                                                  colors.HexColor('#fee2e2')]),
            ('GRID',          (0, 0), (-1, -1), 0.5, colors.HexColor('#fca5a5')),
            ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING',    (0, 0), (-1, -1), padding),
            ('BOTTOMPADDING', (0, 0), (-1, -1), padding),
            ('LEFTPADDING',   (0, 0), (-1, -1), 6),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 6),
        ])

    def _stats_tabla(total_nb, con_alumno, sin_netbook):
        data = [['Total Netbooks', 'Con alumno asignado', 'Sin netbook disponible'],
                [str(total_nb), str(con_alumno), str(sin_netbook)]]
        t = Table(data, colWidths=[5.5*cm, 5.5*cm, 5.5*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, 0),  AZUL_ESCUELA),
            ('TEXTCOLOR',     (0, 0), (-1, 0),  colors.white),
            ('FONTNAME',      (0, 0), (-1, 0),  'Helvetica-Bold'),
            ('FONTSIZE',      (0, 0), (-1, -1), 9),
            ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
            ('BACKGROUND',    (0, 1), (-1, 1),  AZUL_CLARO),
            ('FONTNAME',      (0, 1), (-1, 1),  'Helvetica-Bold'),
            ('GRID',          (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
            ('TOPPADDING',    (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        return t

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                             rightMargin=MARGIN, leftMargin=MARGIN,
                             topMargin=MARGIN, bottomMargin=MARGIN)
    story = []

    netbooks_ord = sorted(carro.netbooks, key=lambda n: (n.numero_interno or '').zfill(10))

    # Detectar cursos asignados en este carro
    cursos_m = sorted({nb.alumno_manana.curso for nb in netbooks_ord if nb.alumno_manana})
    cursos_t = sorted({nb.alumno_tarde.curso  for nb in netbooks_ord if nb.alumno_tarde})

    # ── Datos turno mañana ────────────────────────────────────────────────────
    sin_nb_m = []
    if cursos_m:
        ids_asignados_m = {nb.alumno_manana_id for nb in netbooks_ord if nb.alumno_manana_id}
        sin_nb_m = Alumno.query.filter(
            Alumno.curso.in_(cursos_m),
            Alumno.turno == 'M',
            ~Alumno.id.in_(ids_asignados_m)
        ).order_by(Alumno.apellido, Alumno.nombre).all()

    filas_asig_m = [nb for nb in netbooks_ord if nb.alumno_manana]
    fs_m = _calcular_fs(len(filas_asig_m), len(sin_nb_m))

    # ── TURNO MAÑANA ─────────────────────────────────────────────────────────
    _encabezado(story, f'Asignación Turno Mañana — Carro {carro.display}',
                f'División: {carro.division or "—"} | Aula: {carro.aula or "—"} | Curso: {", ".join(cursos_m) or "—"}')

    con_m = len(filas_asig_m)
    story.append(_stats_tabla(len(netbooks_ord), con_m, len(sin_nb_m)))
    story.append(Spacer(1, 0.4*cm))

    # Tabla asignados mañana — sin columna Curso
    data_m = [['N°', 'Alumno — Turno Mañana']]
    for nb in filas_asig_m:
        data_m.append([
            nb.numero_interno or '—',
            f'{nb.alumno_manana.apellido}, {nb.alumno_manana.nombre}',
        ])
    if len(data_m) > 1:
        col_num  = 2 * cm
        col_nom  = PAGE_W - 2 * MARGIN - col_num
        t_m = Table(data_m, colWidths=[col_num, col_nom])
        t_m.setStyle(_estilo_asig(fs_m))
        story.append(t_m)

    # Tabla sin netbook mañana
    if sin_nb_m:
        story.append(Spacer(1, 0.4*cm))
        story.append(Paragraph(
            'Alumnos sin netbook disponible — Turno Mañana',
            ParagraphStyle('warn_m', parent=styles['Normal'],
                           fontSize=10, fontName='Helvetica-Bold', textColor=ROJO)
        ))
        story.append(Spacer(1, 0.15*cm))
        data_sin_m = [['Apellido y Nombre']]
        for a in sin_nb_m:
            data_sin_m.append([f'{a.apellido}, {a.nombre}'])
        col_full = PAGE_W - 2 * MARGIN
        t_sin_m = Table(data_sin_m, colWidths=[col_full])
        t_sin_m.setStyle(_estilo_sin(fs_m))
        story.append(t_sin_m)

    # ── SALTO DE PÁGINA ───────────────────────────────────────────────────────
    story.append(PageBreak())

    # ── Datos turno tarde ─────────────────────────────────────────────────────
    sin_nb_t = []
    if cursos_t:
        ids_asignados_t = {nb.alumno_tarde_id for nb in netbooks_ord if nb.alumno_tarde_id}
        sin_nb_t = Alumno.query.filter(
            Alumno.curso.in_(cursos_t),
            Alumno.turno == 'T',
            ~Alumno.id.in_(ids_asignados_t)
        ).order_by(Alumno.apellido, Alumno.nombre).all()

    filas_asig_t = [nb for nb in netbooks_ord if nb.alumno_tarde]
    fs_t = _calcular_fs(len(filas_asig_t), len(sin_nb_t))

    # ── TURNO TARDE ──────────────────────────────────────────────────────────
    _encabezado(story, f'Asignación Turno Tarde — Carro {carro.display}',
                f'División: {carro.division or "—"} | Aula: {carro.aula or "—"} | Curso: {", ".join(cursos_t) or "—"}')

    con_t = len(filas_asig_t)
    story.append(_stats_tabla(len(netbooks_ord), con_t, len(sin_nb_t)))
    story.append(Spacer(1, 0.4*cm))

    # Tabla asignados tarde — sin columna Curso
    data_t = [['N°', 'Alumno — Turno Tarde']]
    for nb in filas_asig_t:
        data_t.append([
            nb.numero_interno or '—',
            f'{nb.alumno_tarde.apellido}, {nb.alumno_tarde.nombre}',
        ])
    if len(data_t) > 1:
        col_num = 2 * cm
        col_nom = PAGE_W - 2 * MARGIN - col_num
        t_t = Table(data_t, colWidths=[col_num, col_nom])
        t_t.setStyle(_estilo_asig(fs_t))
        story.append(t_t)

    # Tabla sin netbook tarde
    if sin_nb_t:
        story.append(Spacer(1, 0.4*cm))
        story.append(Paragraph(
            'Alumnos sin netbook disponible — Turno Tarde',
            ParagraphStyle('warn_t', parent=styles['Normal'],
                           fontSize=10, fontName='Helvetica-Bold', textColor=ROJO)
        ))
        story.append(Spacer(1, 0.15*cm))
        data_sin_t = [['Apellido y Nombre']]
        for a in sin_nb_t:
            data_sin_t.append([f'{a.apellido}, {a.nombre}'])
        col_full = PAGE_W - 2 * MARGIN
        t_sin_t = Table(data_sin_t, colWidths=[col_full])
        t_sin_t.setStyle(_estilo_sin(fs_t))
        story.append(t_sin_t)

    doc.build(story)
    buffer.seek(0)
    return buffer


# ─────────────────────────────────────────────────────────────────────────────
#  PDF ASIGNACIÓN — NETBOOK INDIVIDUAL
# ─────────────────────────────────────────────────────────────────────────────

def generar_pdf_asignacion_netbook(netbook):
    """PDF de una netbook individual con sus alumnos de mañana y tarde."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                             rightMargin=1.5*cm, leftMargin=1.5*cm,
                             topMargin=1.5*cm, bottomMargin=1.5*cm)
    story = []
    _encabezado(story, f'Asignación — Netbook {netbook.numero_interno or netbook.id}',
                f'Carro {netbook.carro.display if netbook.carro else "—"}')

    ficha = [
        ['Campo',       'Dato'],
        ['N° Interno',  netbook.numero_interno or '—'],
        ['N° de Serie', netbook.numero_serie or '—'],
        ['Carro',       netbook.carro.display if netbook.carro else '—'],
        ['Estado',      'Operativa' if netbook.estado == 'operativa' else 'Servicio Técnico'],
    ]

    # Turno Mañana
    if netbook.alumno_manana:
        ficha += [
            ['Alumno Mañana', f'{netbook.alumno_manana.apellido}, {netbook.alumno_manana.nombre}'],
            ['DNI Mañana',    netbook.alumno_manana.dni],
            ['Curso Mañana',  netbook.alumno_manana.curso],
        ]
    else:
        ficha.append(['Alumno Mañana', 'Sin asignar'])

    # Turno Tarde
    if netbook.alumno_tarde:
        ficha += [
            ['Alumno Tarde', f'{netbook.alumno_tarde.apellido}, {netbook.alumno_tarde.nombre}'],
            ['DNI Tarde',    netbook.alumno_tarde.dni],
            ['Curso Tarde',  netbook.alumno_tarde.curso],
        ]
    else:
        ficha.append(['Alumno Tarde', 'Sin asignar'])

    t = Table(ficha, colWidths=[4*cm, 13.5*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0),  AZUL_ESCUELA),
        ('TEXTCOLOR',     (0, 0), (-1, 0),  colors.white),
        ('FONTNAME',      (0, 0), (-1, 0),  'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, 0),  10),
        ('BACKGROUND',    (0, 1), (0, -1),  AZUL_CLARO),
        ('FONTNAME',      (0, 1), (0, -1),  'Helvetica-Bold'),
        ('FONTNAME',      (1, 1), (1, -1),  'Helvetica'),
        ('FONTSIZE',      (0, 1), (-1, -1), 10),
        ('ALIGN',         (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID',          (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
        ('TOPPADDING',    (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING',   (0, 0), (-1, -1), 8),
    ]))
    story.append(t)

    doc.build(story)
    buffer.seek(0)
    return buffer


# ─────────────────────────────────────────────────────────────────────────────
#  PDF BAJA DE NETBOOK
# ─────────────────────────────────────────────────────────────────────────────

def generar_pdf_baja_netbook(netbook):
    """PDF de constancia de baja de una netbook con motivo y firma."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                             rightMargin=1.5*cm, leftMargin=1.5*cm,
                             topMargin=1.5*cm, bottomMargin=1.5*cm)
    story = []
    _encabezado(story, f'Constancia de Baja — Netbook {netbook.numero_interno or netbook.id}',
                f'Carro {netbook.carro.display if netbook.carro else "—"}')

    # Alerta visual de baja
    alerta = Table([['⚠️  EQUIPO DADO DE BAJA']], colWidths=[17.5*cm])
    alerta.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), ROJO),
        ('TEXTCOLOR',     (0, 0), (-1, -1), colors.white),
        ('FONTNAME',      (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, -1), 12),
        ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING',    (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(alerta)
    story.append(Spacer(1, 0.4*cm))

    # Datos del equipo
    fecha_baja_str = _arg_full(netbook.fecha_baja)

    ficha = [
        ['Campo',          'Dato'],
        ['N° Interno',     netbook.numero_interno or '—'],
        ['N° de Serie',    netbook.numero_serie or '—'],
        ['Carro',          netbook.carro.display if netbook.carro else '—'],
        ['Fecha de Baja',  fecha_baja_str],
        ['Registrado por', netbook.usuario_baja or '—'],
        ['Motivo de Baja', netbook.motivo_baja or '—'],
    ]

    t = Table(ficha, colWidths=[4.5*cm, 13*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0),  AZUL_ESCUELA),
        ('TEXTCOLOR',     (0, 0), (-1, 0),  colors.white),
        ('FONTNAME',      (0, 0), (-1, 0),  'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, 0),  10),
        ('BACKGROUND',    (0, 1), (0, -1),  AZUL_CLARO),
        ('FONTNAME',      (0, 1), (0, -1),  'Helvetica-Bold'),
        ('BACKGROUND',    (0, 6), (-1, 6),  colors.HexColor('#fee2e2')),
        ('FONTNAME',      (1, 1), (1, -1),  'Helvetica'),
        ('FONTSIZE',      (0, 1), (-1, -1), 10),
        ('ALIGN',         (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID',          (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
        ('TOPPADDING',    (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING',   (0, 0), (-1, -1), 8),
    ]))
    story.append(t)
    story.append(Spacer(1, 1.5*cm))

    # Líneas de firma
    firmas = Table([
        [_campo_firma('Firma del Encargado', 7*cm), '', _campo_firma('Aclaración', 7*cm)]
    ], colWidths=[7.5*cm, 2.5*cm, 7.5*cm])
    story.append(firmas)

    doc.build(story)
    buffer.seek(0)
    return buffer


# ─────────────────────────────────────────────────────────────────────────────
#  PDF INVENTARIO DE NETBOOKS POR CARRO
# ─────────────────────────────────────────────────────────────────────────────

def pdf_inventario_carro(carro):
    """PDF simple: N° Interno y N° de Serie de todas las netbooks del carro."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                             rightMargin=1.5*cm, leftMargin=1.5*cm,
                             topMargin=1.5*cm, bottomMargin=1.5*cm)
    story = []
    _encabezado(story, f'Inventario — Carro {carro.display}',
                f'División: {carro.division or "—"} | Aula: {carro.aula or "—"}')

    data = [['N° Interno', 'N° de Serie', 'Estado']]
    netbooks_ord = sorted(carro.netbooks, key=lambda n: (n.numero_interno or '').zfill(10))
    for nb in netbooks_ord:
        if nb.estado == 'operativa':
            estado = 'Operativa'
        elif nb.estado == 'servicio_tecnico':
            estado = 'Servicio Técnico'
        else:
            estado = nb.estado
        data.append([
            nb.numero_interno or '—',
            nb.numero_serie or 'SIN SERIE',
            estado,
        ])

    t = Table(data, colWidths=[4*cm, 10*cm, 4*cm])
    t.setStyle(_tabla_estilo())
    story.append(t)
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(f'Total: {len(data)-1} netbook(s)', STYLE_NORMAL))

    doc.build(story)
    buffer.seek(0)
    return buffer


# ─────────────────────────────────────────────────────────────────────────────
#  PDF TICKETS BA COLABORATIVA
# ─────────────────────────────────────────────────────────────────────────────

def pdf_tickets_ba(tickets):
    """
    PDF de tickets BA Colaborativa.
    tickets: lista de objetos TicketBA con sus netbooks en servicio.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                             rightMargin=1.5*cm, leftMargin=1.5*cm,
                             topMargin=1.5*cm, bottomMargin=1.5*cm)
    story = []
    _encabezado(story, 'Tickets BA Colaborativa',
                f'Netbooks en Servicio Técnico — {len(tickets)} ticket(s)')

    for ticket in tickets:
        story.append(Spacer(1, 0.3*cm))

        # Encabezado del ticket
        header = Table([[
            Paragraph(f'Ticket #{ticket.id} — {_arg_full(ticket.fecha_creacion)}', STYLE_SECCION),
        ]], colWidths=[17.5*cm])
        header.setStyle(TableStyle([
            ('BACKGROUND',    (0,0), (-1,-1), AZUL_CLARO),
            ('LEFTPADDING',   (0,0), (-1,-1), 8),
            ('TOPPADDING',    (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('BOX',           (0,0), (-1,-1), 0.5, AZUL_ESCUELA),
        ]))
        story.append(header)

        # Datos del ticket
        ficha = [
            ['N° Reclamo BA',   ticket.nro_reclamo or '—',
             'Registrado por',  ticket.usuario or '—'],
            ['Observaciones',   ticket.observaciones or '—',
             'Fecha',           _arg_full(ticket.fecha_creacion)],
        ]
        t_ficha = Table(ficha, colWidths=[3.5*cm, 5.5*cm, 3.5*cm, 5*cm])
        t_ficha.setStyle(TableStyle([
            ('BACKGROUND',    (0,0), (0,-1), AZUL_CLARO),
            ('BACKGROUND',    (2,0), (2,-1), AZUL_CLARO),
            ('FONTNAME',      (0,0), (0,-1), 'Helvetica-Bold'),
            ('FONTNAME',      (2,0), (2,-1), 'Helvetica-Bold'),
            ('FONTSIZE',      (0,0), (-1,-1), 9),
            ('GRID',          (0,0), (-1,-1), 0.5, colors.HexColor('#e5e7eb')),
            ('TOPPADDING',    (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING',   (0,0), (-1,-1), 6),
            ('VALIGN',        (0,0), (-1,-1), 'TOP'),
        ]))
        story.append(t_ficha)

        # Netbooks del ticket
        story.append(Spacer(1, 0.2*cm))
        data_nb = [['Carro', 'N° Interno', 'N° Serie', 'Problema']]
        for item in ticket.netbooks:
            nb = item.netbook
            if not nb:
                continue
            data_nb.append([
                nb.carro.display if nb.carro else '—',
                nb.numero_interno or '—',
                nb.numero_serie or '—',
                Paragraph(nb.problema or '—', STYLE_NORMAL),
            ])
        t_nb = Table(data_nb, colWidths=[3*cm, 3*cm, 5.5*cm, 6*cm])
        t_nb.setStyle(_tabla_estilo(NARANJA))
        story.append(t_nb)
        story.append(HRFlowable(width='100%', thickness=0.5,
                                color=colors.HexColor('#e5e7eb')))

    doc.build(story)
    buffer.seek(0)
    return buffer


# ─────────────────────────────────────────────────────────────────────────────
#  PDF PARTE DE ALERTA — PRÉSTAMO EN DEMORA
# ─────────────────────────────────────────────────────────────────────────────

ROJO_CLARO    = colors.HexColor('#fee2e2')
NARANJA_CLARO = colors.HexColor('#fff7ed')

STYLE_ALERTA_TITULO = ParagraphStyle('AlertaTitulo', parent=styles['Normal'],
    fontSize=13, fontName='Helvetica-Bold',
    textColor=colors.white, alignment=TA_CENTER)

STYLE_NOTA = ParagraphStyle('Nota', parent=styles['Normal'],
    fontSize=8, fontName='Helvetica-Oblique',
    textColor=colors.HexColor('#6b7280'), alignment=TA_CENTER)


def _banner_demora(story, tiempo_str):
    """Banner rojo con el tiempo de demora."""
    banner = Table([[Paragraph(
        f'DEMORA DETECTADA — {tiempo_str} sin devolver',
        STYLE_ALERTA_TITULO)]], colWidths=[17.5*cm])
    banner.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), ROJO),
        ('TOPPADDING',    (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING',   (0, 0), (-1, -1), 8),
    ]))
    story.append(banner)
    story.append(Spacer(1, 0.5*cm))


def _tabla_docente(story, docente):
    """Bloque de datos del docente."""
    story.append(Paragraph('DATOS DEL DOCENTE', STYLE_SECCION))
    doc_data = [
        ['Apellido y Nombre', docente.nombre_completo if docente else '—'],
        ['DNI',               docente.dni if docente else '—'],
        ['Materia',           (docente.materia or '—') if docente else '—'],
        ['Turno',             (docente.turno or '—') if docente else '—'],
        ['Correo',            (docente.correo or '—') if docente else '—'],
    ]
    t = Table(doc_data, colWidths=[4.5*cm, 13*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (0, -1), AZUL_CLARO),
        ('FONTNAME',      (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME',      (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE',      (0, 0), (-1, -1), 9),
        ('GRID',          (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
        ('TOPPADDING',    (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING',   (0, 0), (-1, -1), 8),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.5*cm))


def _bloque_firmas(story, ahora_arg):
    """Tres líneas de firma al pie."""
    story.append(Spacer(1, 1.2*cm))
    story.append(HRFlowable(width='100%', thickness=0.5, color=colors.HexColor('#e5e7eb')))
    story.append(Spacer(1, 0.5*cm))
    firmas = Table([[
        _campo_firma('Encargado/a', 5*cm),
        '',
        _campo_firma('Docente notificado/a', 5*cm),
        '',
        _campo_firma('Directivo/a (si aplica)', 5*cm),
    ]], colWidths=[5.2*cm, 0.7*cm, 5.2*cm, 0.7*cm, 5.2*cm])
    firmas.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN',  (0, 0), (-1, -1), 'CENTER'),
    ]))
    story.append(firmas)
    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph(
        f'Parte generado el {ahora_arg.strftime("%d/%m/%Y a las %H:%M")} hs'
        f'  ·  SIGA-Tec — E.T. N°7 D.E. 5',
        STYLE_NOTA))


def pdf_alerta_demora_carro(prestamo_id):
    """
    Parte de Alerta para un préstamo de CARRO en demora.
    Incluye datos del docente, datos del préstamo y listado completo
    de netbooks del carro (N° interno + N° de serie).
    """
    from models import PrestamoCarro
    prestamo   = PrestamoCarro.query.get_or_404(prestamo_id)
    ahora_arg  = datetime.utcnow() + ARG_OFFSET
    retiro_arg = prestamo.hora_retiro + ARG_OFFSET
    delta_mins = int((datetime.utcnow() - prestamo.hora_retiro).total_seconds() / 60)
    horas, mins = delta_mins // 60, delta_mins % 60
    tiempo_str = f'{horas}h {mins}m' if horas else f'{mins}m'

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                             rightMargin=1.5*cm, leftMargin=1.5*cm,
                             topMargin=1.5*cm, bottomMargin=1.5*cm)
    story = []
    _encabezado(story, 'PARTE DE ALERTA — PRÉSTAMO EN DEMORA',
                'Préstamo de Carro de Netbooks')
    story.append(Spacer(1, 0.3*cm))
    _banner_demora(story, tiempo_str)

    # ── Docente ───────────────────────────────────────────────────
    _tabla_docente(story, prestamo.docente)

    # ── Préstamo / Carro ──────────────────────────────────────────
    story.append(Paragraph('DATOS DEL PRÉSTAMO', STYLE_SECCION))
    prest_data = [
        ['Código',             prestamo.codigo or '—'],
        ['Carro',              prestamo.carro.display if prestamo.carro else '—'],
        ['División',           (prestamo.carro.division or '—') if prestamo.carro else '—'],
        ['Aula',               prestamo.aula or ((prestamo.carro.aula or '—') if prestamo.carro else '—')],
        ['Hora de Retiro',     retiro_arg.strftime('%d/%m/%Y  %H:%M')],
        ['Tiempo Transcurrido', tiempo_str],
        ['Registrado por',     prestamo.encargado_retiro or '—'],
    ]
    t_prest = Table(prest_data, colWidths=[4.5*cm, 13*cm])
    estilo_prest = TableStyle([
        ('BACKGROUND',    (0, 0), (0, -1), AZUL_CLARO),
        ('FONTNAME',      (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME',      (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE',      (0, 0), (-1, -1), 9),
        ('GRID',          (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
        ('TOPPADDING',    (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING',   (0, 0), (-1, -1), 8),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        # fila "Tiempo Transcurrido" (índice 5) resaltada en naranja
        ('BACKGROUND',    (1, 5), (1, 5), NARANJA_CLARO),
        ('TEXTCOLOR',     (1, 5), (1, 5), NARANJA),
        ('FONTNAME',      (1, 5), (1, 5), 'Helvetica-Bold'),
        ('FONTSIZE',      (1, 5), (1, 5), 11),
    ])
    t_prest.setStyle(estilo_prest)
    story.append(t_prest)
    story.append(Spacer(1, 0.5*cm))

    # ── Netbooks del carro ────────────────────────────────────────
    if prestamo.carro and prestamo.carro.netbooks:
        story.append(Paragraph(
            f'NETBOOKS DEL CARRO {prestamo.carro.display} '
            f'({prestamo.carro.total_netbooks} equipo(s))',
            STYLE_SECCION))
        nb_data = [['N°', 'N° Interno', 'N° de Serie', 'Alumno Asignado', 'Estado']]
        netbooks_ord = sorted(prestamo.carro.netbooks,
                              key=lambda n: (n.numero_interno or '').zfill(10))
        for i, nb in enumerate(netbooks_ord, start=1):
            estado_nb = 'Operativa' if nb.estado == 'operativa' else 'Serv. Téc.'
            nb_data.append([
                str(i),
                nb.numero_interno or '—',
                nb.numero_serie or '—',
                nb.alumno or '—',
                estado_nb,
            ])
        t_nb = Table(nb_data, colWidths=[0.8*cm, 2.5*cm, 5.5*cm, 6.7*cm, 2*cm])
        estilo_nb = _tabla_estilo()
        for i, nb in enumerate(netbooks_ord, start=1):
            if nb.estado != 'operativa':
                estilo_nb.add('TEXTCOLOR', (4, i), (4, i), NARANJA)
                estilo_nb.add('FONTNAME',  (4, i), (4, i), 'Helvetica-Bold')
        t_nb.setStyle(estilo_nb)
        story.append(t_nb)
        story.append(Spacer(1, 0.3*cm))
        story.append(Paragraph(
            f'Total: {prestamo.carro.total_netbooks}  ·  '
            f'Operativas: {prestamo.carro.operativas}  ·  '
            f'En servicio: {prestamo.carro.en_servicio}',
            STYLE_NORMAL))

    _bloque_firmas(story, ahora_arg)
    doc.build(story)
    buffer.seek(0)
    nombre = (f'alerta_demora_carro_'
              f'{prestamo.carro.numero_fisico if prestamo.carro else prestamo.id}.pdf')
    return send_file(buffer, as_attachment=True,
                     download_name=nombre, mimetype='application/pdf')


def pdf_alerta_demora_netbooks(prestamo_id):
    """
    Parte de Alerta para un préstamo de NETBOOKS (Espacio Digital) en demora.
    Incluye datos del docente, datos del préstamo y listado individual de
    cada netbook (N° interno + N° de serie + alumno asignado).
    """
    from models import PrestamoNetbook
    prestamo   = PrestamoNetbook.query.get_or_404(prestamo_id)
    ahora_arg  = datetime.utcnow() + ARG_OFFSET
    retiro_arg = prestamo.hora_retiro + ARG_OFFSET
    delta_mins = int((datetime.utcnow() - prestamo.hora_retiro).total_seconds() / 60)
    horas, mins = delta_mins // 60, delta_mins % 60
    tiempo_str = f'{horas}h {mins}m' if horas else f'{mins}m'

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                             rightMargin=1.5*cm, leftMargin=1.5*cm,
                             topMargin=1.5*cm, bottomMargin=1.5*cm)
    story = []
    _encabezado(story, 'PARTE DE ALERTA — PRÉSTAMO EN DEMORA',
                'Espacio Digital — Préstamo de Netbooks Individuales')
    story.append(Spacer(1, 0.3*cm))
    _banner_demora(story, tiempo_str)

    # ── Docente ───────────────────────────────────────────────────
    _tabla_docente(story, prestamo.docente)

    # ── Préstamo ──────────────────────────────────────────────────
    story.append(Paragraph('DATOS DEL PRÉSTAMO', STYLE_SECCION))
    prest_data = [
        ['Código',              prestamo.codigo or '—'],
        ['Cantidad de Netbooks', str(len(prestamo.items))],
        ['Hora de Retiro',      retiro_arg.strftime('%d/%m/%Y  %H:%M')],
        ['Tiempo Transcurrido', tiempo_str],
        ['Registrado por',      prestamo.encargado_retiro or '—'],
    ]
    t_prest = Table(prest_data, colWidths=[4.5*cm, 13*cm])
    estilo_prest = TableStyle([
        ('BACKGROUND',    (0, 0), (0, -1), AZUL_CLARO),
        ('FONTNAME',      (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME',      (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE',      (0, 0), (-1, -1), 9),
        ('GRID',          (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
        ('TOPPADDING',    (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING',   (0, 0), (-1, -1), 8),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        # fila "Tiempo Transcurrido" (índice 3) resaltada en naranja
        ('BACKGROUND',    (1, 3), (1, 3), NARANJA_CLARO),
        ('TEXTCOLOR',     (1, 3), (1, 3), NARANJA),
        ('FONTNAME',      (1, 3), (1, 3), 'Helvetica-Bold'),
        ('FONTSIZE',      (1, 3), (1, 3), 11),
    ])
    t_prest.setStyle(estilo_prest)
    story.append(t_prest)
    story.append(Spacer(1, 0.5*cm))

    # ── Netbooks prestadas ────────────────────────────────────────
    if prestamo.items:
        story.append(Paragraph(
            f'NETBOOKS PRESTADAS ({len(prestamo.items)} equipo(s))',
            STYLE_SECCION))
        nb_data = [['N°', 'N° Interno', 'N° de Serie', 'Alumno Asignado']]
        for i, item in enumerate(prestamo.items, start=1):
            nb_data.append([
                str(i),
                item.numero_interno or '—',
                item.numero_serie or '—',
                item.alumno or '—',
            ])
        t_nb = Table(nb_data, colWidths=[0.8*cm, 2.5*cm, 6*cm, 8.2*cm])
        t_nb.setStyle(_tabla_estilo())
        story.append(t_nb)

    _bloque_firmas(story, ahora_arg)
    doc.build(story)
    buffer.seek(0)
    nombre = f'alerta_demora_espacio_digital_{prestamo.id}.pdf'
    return send_file(buffer, as_attachment=True,
                     download_name=nombre, mimetype='application/pdf')


# ─────────────────────────────────────────────────────────────────────────────
#  PLANILLA DE MOVIMIENTOS ACTIVOS — para conducción
# ─────────────────────────────────────────────────────────────────────────────

def pdf_movimientos_activos(como_buffer=False):
    """
    Genera la Planilla de Movimientos Activos con todos los préstamos activos
    (carros + Espacio Digital) con casilleros para tildar devoluciones a mano.
    Orientación: landscape (A4 horizontal).
    Si como_buffer=True devuelve el BytesIO en lugar de un send_file()
    (usado para adjuntar al mail).
    """
    from models import PrestamoCarro, PrestamoNetbook
    from reportlab.lib.pagesizes import landscape

    ahora_arg = datetime.utcnow() + ARG_OFFSET

    prestamos_carros   = PrestamoCarro.query.filter_by(estado='activo').order_by(PrestamoCarro.hora_retiro).all()
    prestamos_netbooks = PrestamoNetbook.query.filter_by(estado='activo').order_by(PrestamoNetbook.hora_retiro).all()

    # Ancho útil landscape A4 ≈ 25.7 cm
    ANCHO_UTIL = 25.7*cm

    STYLE_NOTA = ParagraphStyle('MovNota', parent=styles['Normal'],
        fontSize=7, fontName='Helvetica', textColor=colors.grey, alignment=TA_CENTER)
    STYLE_CHICO = ParagraphStyle('MovChico', parent=styles['Normal'],
        fontSize=8, fontName='Helvetica')
    STYLE_CHICO_BOLD = ParagraphStyle('MovChicoBold', parent=styles['Normal'],
        fontSize=8, fontName='Helvetica-Bold')
    ROJO_CLARO  = colors.HexColor('#fee2e2')
    VERDE_CLARO = colors.HexColor('#dcfce7')

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4),
                             rightMargin=1.5*cm, leftMargin=1.5*cm,
                             topMargin=1.5*cm, bottomMargin=1.5*cm)
    story = []

    _encabezado(story,
                'PLANILLA DE MOVIMIENTOS ACTIVOS',
                f'Generada el {ahora_arg.strftime("%d/%m/%Y a las %H:%M")} hs')

    # ── Aviso de uso ─────────────────────────────────────────────────────────
    aviso = Table([[Paragraph(
        'Esta planilla lista todos los préstamos activos al momento de su generación. '
        'Usarla para tildar devoluciones cuando el encargado no esté presente.',
        ParagraphStyle('MovAviso', parent=styles['Normal'],
            fontSize=9, fontName='Helvetica', textColor=colors.HexColor('#92400e')))
    ]], colWidths=[ANCHO_UTIL])
    aviso.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), colors.HexColor('#fef3c7')),
        ('BOX',           (0, 0), (-1, -1), 1, colors.HexColor('#d97706')),
        ('TOPPADDING',    (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING',   (0, 0), (-1, -1), 10),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 10),
    ]))
    story.append(aviso)
    story.append(Spacer(1, 0.5*cm))

    # ═══════════════════════════════════════════════════════════════════════════
    # SECCIÓN 1 — PRÉSTAMOS DE CARROS
    # ═══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph('PRÉSTAMOS DE CARROS DE NETBOOKS', STYLE_SECCION))
    story.append(Spacer(1, 0.2*cm))

    if prestamos_carros:
        cab = [
            Paragraph('Carro', STYLE_CHICO_BOLD),
            Paragraph('Docente', STYLE_CHICO_BOLD),
            Paragraph('Materia', STYLE_CHICO_BOLD),
            Paragraph('Aula', STYLE_CHICO_BOLD),
            Paragraph('Hora Retiro', STYLE_CHICO_BOLD),
            Paragraph('Registró', STYLE_CHICO_BOLD),
            Paragraph('Devuelto ✓', STYLE_CHICO_BOLD),
        ]
        data_c = [cab]
        for p in prestamos_carros:
            retiro_str = (p.hora_retiro + ARG_OFFSET).strftime('%H:%M')
            data_c.append([
                Paragraph(p.carro.display if p.carro else '—', STYLE_CHICO),
                Paragraph(p.docente.nombre_completo if p.docente else '—', STYLE_CHICO),
                Paragraph(p.docente.materia or '—' if p.docente else '—', STYLE_CHICO),
                Paragraph(p.aula or (p.carro.aula if p.carro else '—') or '—', STYLE_CHICO),
                Paragraph(retiro_str, STYLE_CHICO),
                Paragraph(p.encargado_retiro or '—', STYLE_CHICO),
                '',  # casillero en blanco para tildar a mano
            ])

        # landscape: 7 columnas en 25.7 cm
        t_c = Table(data_c, colWidths=[2.8*cm, 5.5*cm, 5*cm, 2*cm, 2.5*cm, 5.5*cm, 2.4*cm])
        estilo_c = TableStyle([
            ('BACKGROUND',    (0, 0), (-1, 0),  AZUL_ESCUELA),
            ('TEXTCOLOR',     (0, 0), (-1, 0),  colors.white),
            ('FONTNAME',      (0, 0), (-1, 0),  'Helvetica-Bold'),
            ('FONTSIZE',      (0, 0), (-1, 0),  8),
            ('ALIGN',         (0, 0), (-1, 0),  'CENTER'),
            ('FONTNAME',      (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE',      (0, 1), (-1, -1), 8),
            ('ROWBACKGROUNDS',(0, 1), (-1, -1), [colors.white, GRIS_CLARO]),
            ('GRID',          (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
            ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING',    (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING',   (0, 0), (-1, -1), 5),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 5),
            ('ALIGN',         (6, 0), (6, -1), 'CENTER'),
            ('BACKGROUND',    (6, 1), (6, -1), VERDE_CLARO),
        ])
        for i, p in enumerate(prestamos_carros, start=1):
            delta_mins = int((datetime.utcnow() - p.hora_retiro).total_seconds() / 60)
            if delta_mins >= 120:
                estilo_c.add('BACKGROUND', (0, i), (5, i), ROJO_CLARO)
                estilo_c.add('TEXTCOLOR',  (0, i), (5, i), colors.HexColor('#991b1b'))
        t_c.setStyle(estilo_c)
        story.append(t_c)
        story.append(Spacer(1, 0.2*cm))
        story.append(Paragraph(
            f'Total préstamos de carros activos: {len(prestamos_carros)}  ·  '
            'Las filas en rojo superan las 2 horas de préstamo.',
            STYLE_NOTA))
    else:
        cuadro_vacio = Table([[Paragraph(
            'No hay préstamos de carros activos al momento de generar esta planilla.',
            ParagraphStyle('MovV', parent=styles['Normal'], fontSize=9,
                           fontName='Helvetica', textColor=colors.grey, alignment=TA_CENTER))
        ]], colWidths=[ANCHO_UTIL])
        cuadro_vacio.setStyle(TableStyle([
            ('BACKGROUND',    (0,0), (-1,-1), GRIS_CLARO),
            ('BOX',           (0,0), (-1,-1), 0.5, colors.HexColor('#d1d5db')),
            ('TOPPADDING',    (0,0), (-1,-1), 10),
            ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ]))
        story.append(cuadro_vacio)

    story.append(Spacer(1, 0.7*cm))

    # ═══════════════════════════════════════════════════════════════════════════
    # SECCIÓN 2 — ESPACIO DIGITAL
    # ═══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph('ESPACIO DIGITAL — PRÉSTAMOS DE NETBOOKS INDIVIDUALES', STYLE_SECCION))
    story.append(Spacer(1, 0.2*cm))

    if prestamos_netbooks:
        for p in prestamos_netbooks:
            delta_mins = int((datetime.utcnow() - p.hora_retiro).total_seconds() / 60)
            retiro_str = (p.hora_retiro + ARG_OFFSET).strftime('%H:%M')
            demora     = delta_mins >= 120

            color_fondo = ROJO_CLARO if demora else AZUL_CLARO
            color_texto = colors.HexColor('#991b1b') if demora else AZUL_ESCUELA
            encab_prest = Table([[
                Paragraph(
                    f'<b>{p.docente.nombre_completo if p.docente else "—"}</b>'
                    f'  ·  {p.docente.materia or "—" if p.docente else "—"}'
                    f'  ·  Retiro: {retiro_str}'
                    f'  ·  Registró: {p.encargado_retiro or "—"}'
                    f'  ·  Código: {p.codigo or "—"}'
                    + ('  ⚠️ DEMORA' if demora else ''),
                    ParagraphStyle('MovEP', parent=styles['Normal'],
                        fontSize=8, fontName='Helvetica-Bold', textColor=color_texto))
            ]], colWidths=[ANCHO_UTIL])
            encab_prest.setStyle(TableStyle([
                ('BACKGROUND',    (0,0), (-1,-1), color_fondo),
                ('BOX',           (0,0), (-1,-1), 0.5, color_texto),
                ('TOPPADDING',    (0,0), (-1,-1), 5),
                ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                ('LEFTPADDING',   (0,0), (-1,-1), 8),
            ]))
            story.append(encab_prest)

            # Tabla de netbooks — 5 columnas en 25.7 cm
            cab_nb = [
                Paragraph('N°', STYLE_CHICO_BOLD),
                Paragraph('N° Interno', STYLE_CHICO_BOLD),
                Paragraph('N° de Serie', STYLE_CHICO_BOLD),
                Paragraph('Alumno Asignado', STYLE_CHICO_BOLD),
                Paragraph('Devuelto ✓', STYLE_CHICO_BOLD),
            ]
            data_nb = [cab_nb]
            for i, item in enumerate(p.items, start=1):
                data_nb.append([
                    str(i),
                    item.numero_interno or '—',
                    item.numero_serie or '—',
                    Paragraph(item.alumno or '—', STYLE_CHICO),
                    '',
                ])
            t_nb = Table(data_nb, colWidths=[0.8*cm, 3*cm, 7*cm, 12.4*cm, 2.5*cm])
            estilo_nb = TableStyle([
                ('BACKGROUND',    (0, 0), (-1, 0),  AZUL_ESCUELA),
                ('TEXTCOLOR',     (0, 0), (-1, 0),  colors.white),
                ('FONTNAME',      (0, 0), (-1, 0),  'Helvetica-Bold'),
                ('FONTSIZE',      (0, 0), (-1, 0),  8),
                ('ALIGN',         (0, 0), (-1, 0),  'CENTER'),
                ('FONTNAME',      (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE',      (0, 1), (-1, -1), 8),
                ('ROWBACKGROUNDS',(0, 1), (-1, -1), [colors.white, GRIS_CLARO]),
                ('GRID',          (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
                ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING',    (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('LEFTPADDING',   (0, 0), (-1, -1), 5),
                ('RIGHTPADDING',  (0, 0), (-1, -1), 5),
                ('ALIGN',         (0, 1), (0, -1), 'CENTER'),
                ('ALIGN',         (4, 0), (4, -1), 'CENTER'),
                ('BACKGROUND',    (4, 1), (4, -1), VERDE_CLARO),
            ])
            t_nb.setStyle(estilo_nb)
            story.append(t_nb)
            story.append(Spacer(1, 0.4*cm))

        story.append(Paragraph(
            f'Total préstamos del Espacio Digital activos: {len(prestamos_netbooks)}',
            STYLE_NOTA))
    else:
        cuadro_vacio2 = Table([[Paragraph(
            'No hay préstamos del Espacio Digital activos al momento de generar esta planilla.',
            ParagraphStyle('MovV2', parent=styles['Normal'], fontSize=9,
                           fontName='Helvetica', textColor=colors.grey, alignment=TA_CENTER))
        ]], colWidths=[ANCHO_UTIL])
        cuadro_vacio2.setStyle(TableStyle([
            ('BACKGROUND',    (0,0), (-1,-1), GRIS_CLARO),
            ('BOX',           (0,0), (-1,-1), 0.5, colors.HexColor('#d1d5db')),
            ('TOPPADDING',    (0,0), (-1,-1), 10),
            ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ]))
        story.append(cuadro_vacio2)

    # ── Pie sin firmas ───────────────────────────────────────────────────────
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(
        f'SIGA-Tec — E.T. N°7 D.E. 5  ·  Planilla generada el '
        f'{ahora_arg.strftime("%d/%m/%Y a las %H:%M")} hs',
        STYLE_NOTA))

    doc.build(story)
    buffer.seek(0)

    if como_buffer:
        return buffer

    nombre = f'movimientos_activos_{ahora_arg.strftime("%Y%m%d_%H%M")}.pdf'
    return send_file(buffer, as_attachment=True,
                     download_name=nombre, mimetype='application/pdf')


# ─────────────────────────────────────────────────────────────────────────────
#  PDF HORARIO DE DOCENTE CON CARRO ASIGNADO
# ─────────────────────────────────────────────────────────────────────────────

def pdf_horario_docente(docente):
    """
    PDF landscape A4 — horario del docente con carro asignado por curso.
    - Todo en una sola hoja
    - Sin distinción de color para EXTRA CLASES
    - Fila de títulos única arriba, franjas azules por día
    - Sin firmas al pie
    """
    import re
    from reportlab.lib.pagesizes import landscape
    from itertools import groupby
    from models import Carro
    from models_extra.horarios_notificaciones import HorarioDocente, MODULOS, DIAS_SEMANA

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=1.2*cm, leftMargin=1.2*cm,
        topMargin=1.2*cm, bottomMargin=1.2*cm
    )
    story = []

    _encabezado(
        story,
        titulo=f'HORARIO — {docente.apellido.upper()} {docente.nombre.upper()}',
        subtitulo=f'Materia/s: {docente.materia or "—"}  |  Turno: {docente.turno or "—"}'
    )
    story.append(Spacer(1, 0.3*cm))

    horarios = HorarioDocente.query.filter_by(docente_id=docente.id)\
        .order_by(HorarioDocente.dia, HorarioDocente.modulo).all()

    if not horarios:
        story.append(Paragraph('Este docente no tiene horarios cargados.', STYLE_NORMAL))
        doc.build(story)
        return _generar_response(buffer, f'horario_{docente.apellido.lower()}_{docente.nombre.lower()}.pdf')

    # ── Normalizar curso: GxNy → NxGy ──
    def _norm(s):
        s = s.strip().upper().replace(' ', '')
        m = re.match(r'G(\d+)N(\d+)$', s)
        if m:
            return f'N{m.group(2)}G{m.group(1)}'
        return s

    # ── Índice carro ──
    todos_los_carros = Carro.query.filter(Carro.estado != 'baja').all()
    carros_por_curso = {}
    for c in todos_los_carros:
        if not c.division:
            continue
        for parte in re.split(r'[/,\s]+', c.division.strip().upper()):
            parte = parte.strip()
            if parte:
                carros_por_curso[_norm(parte)] = c
                carros_por_curso[parte] = c

    # ── Ordenar ──
    DIAS_ORDEN = {d: i for i, d in enumerate(DIAS_SEMANA)}
    horarios_ord = sorted(horarios, key=lambda x: (DIAS_ORDEN.get(x.dia, 99), x.modulo))

    # ── Estilos compactos ──
    STYLE_MINI = ParagraphStyle('Mini', parent=styles['Normal'],
        fontSize=7, fontName='Helvetica', leading=9)
    STYLE_DIA_HDR = ParagraphStyle('DiaHdr', parent=styles['Normal'],
        fontSize=8, fontName='Helvetica-Bold', textColor=colors.white, alignment=TA_CENTER)
    STYLE_TITULO_COL = ParagraphStyle('TituloCol', parent=styles['Normal'],
        fontSize=8, fontName='Helvetica-Bold', textColor=colors.white, alignment=TA_CENTER)

    # landscape A4 útil ≈ 27.3cm con márgenes 1.2cm
    col_widths = [1.6*cm, 3.0*cm, 7.2*cm, 2.2*cm, 13.3*cm]

    # ── Fila de títulos ──
    fila_titulos = Table([[
        Paragraph('MÓD.',    STYLE_TITULO_COL),
        Paragraph('HORARIO', STYLE_TITULO_COL),
        Paragraph('MATERIA', STYLE_TITULO_COL),
        Paragraph('CURSO',   STYLE_TITULO_COL),
        Paragraph('CARRO',   STYLE_TITULO_COL),
    ]], colWidths=col_widths)
    fila_titulos.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0), AZUL_ESCUELA),
        ('TOPPADDING',    (0, 0), (-1, 0), 4),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 4),
        ('LEFTPADDING',   (0, 0), (-1, 0), 4),
        ('RIGHTPADDING',  (0, 0), (-1, 0), 4),
    ]))
    story.append(fila_titulos)

    # ── Bloques por día ──
    for dia, items_iter in groupby(horarios_ord, key=lambda x: x.dia):
        items = list(items_iter)

        # Franja azul con nombre del día
        franja_dia = Table([[Paragraph(dia.upper(), STYLE_DIA_HDR), '', '', '', '']],
                            colWidths=col_widths)
        franja_dia.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, 0), colors.HexColor('#1e3a6e')),
            ('SPAN',          (0, 0), (-1, 0)),
            ('TOPPADDING',    (0, 0), (-1, 0), 3),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 3),
        ]))
        story.append(franja_dia)

        # Filas de módulos
        filas_dia = []
        for h in items:
            modulo_info = MODULOS.get(h.modulo, ('—', '—', '—', '—'))
            horario_str = f'{modulo_info[0]} - {modulo_info[1]}'
            codigo_mod  = modulo_info[3]

            curso = _norm(h.aula or '')
            carro = carros_por_curso.get(curso)
            if not carro and h.aula:
                carro = carros_por_curso.get((h.aula or '').strip().upper())

            if carro:
                carro_str = f'Carro N° {carro.numero_fisico}'
                if carro.aula:
                    carro_str += f' — Aula {carro.aula}'
            elif curso:
                carro_str = 'Sin carro asignado'
            else:
                carro_str = '—'

            filas_dia.append([
                Paragraph(codigo_mod,       STYLE_MINI),
                Paragraph(horario_str,      STYLE_MINI),
                Paragraph(h.materia or '—', STYLE_MINI),
                Paragraph(h.aula or '—',    STYLE_MINI),
                Paragraph(carro_str,        STYLE_MINI),
            ])

        tabla_dia = Table(filas_dia, colWidths=col_widths)
        tabla_dia.setStyle(TableStyle([
            ('FONTNAME',      (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE',      (0, 0), (-1, -1), 7),
            ('ROWBACKGROUNDS',(0, 0), (-1, -1), [colors.white, GRIS_CLARO]),
            ('GRID',          (0, 0), (-1, -1), 0.4, colors.HexColor('#e5e7eb')),
            ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING',    (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING',   (0, 0), (-1, -1), 4),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 4),
        ]))
        story.append(tabla_dia)

    doc.build(story)
    nombre_archivo = f'horario_{docente.apellido.lower()}_{docente.nombre.lower()}.pdf'
    return _generar_response(buffer, nombre_archivo)
# ─────────────────────────────────────────────────────────────────────────────
#  PDF CONTROL MASIVO DE STOCK
# ─────────────────────────────────────────────────────────────────────────────

def pdf_control_masivo_stock(resultado):
    """
    PDF con el resultado del control masivo de stock.
    Contiene tres secciones:
      1. Resumen general
      2. Series NO encontradas en el sistema  (lista de números)
      3. Netbooks en el sistema ausentes del listado  (tabla con datos)
      4. Netbooks encontradas (tabla completa)
    Orientación landscape para que entren bien las tablas.
    """
    from reportlab.lib.pagesizes import landscape

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=1.5*cm, leftMargin=1.5*cm,
        topMargin=1.5*cm,  bottomMargin=1.5*cm,
    )
    story = []

    _encabezado(
        story,
        titulo='CONTROL MASIVO DE STOCK — NETBOOKS',
        subtitulo=f'Realizado el {resultado["fecha"]} por {resultado["usuario"]}',
    )
    story.append(Spacer(1, 0.3*cm))

    # ── Resumen ───────────────────────────────────────────────────────────────
    ANCHO = 27.7*cm   # landscape A4 con márgenes 1.5cm ≈ 24.7cm útil
    ANCHO_UTIL = 24.7*cm

    resumen_data = [
        ['Series en el listado', 'Netbooks en el sistema',
         'Encontradas ✅', 'No encontradas ❌', 'Ausentes del listado ⚠️'],
        [
            str(resultado['total_listado']),
            str(resultado['total_sistema']),
            str(len(resultado['encontradas'])),
            str(len(resultado['no_encontradas'])),
            str(len(resultado['no_en_listado'])),
        ]
    ]
    col_res = [ANCHO_UTIL / 5] * 5
    t_res = Table(resumen_data, colWidths=col_res)
    t_res.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0),  AZUL_CLARO),
        ('TEXTCOLOR',     (0, 0), (-1, 0),  AZUL_ESCUELA),
        ('FONTNAME',      (0, 0), (-1, 0),  'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, 0),  8),
        ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME',      (0, 1), (-1, 1),  'Helvetica-Bold'),
        ('FONTSIZE',      (0, 1), (-1, 1),  18),
        ('TEXTCOLOR',     (2, 1), (2, 1),   VERDE),
        ('TEXTCOLOR',     (3, 1), (3, 1),   ROJO),
        ('TEXTCOLOR',     (4, 1), (4, 1),   NARANJA),
        ('GRID',          (0, 0), (-1, -1), 0.5, colors.HexColor('#93c5fd')),
        ('TOPPADDING',    (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t_res)
    story.append(Spacer(1, 0.5*cm))

    STYLE_SEC = ParagraphStyle('SecMasivo', parent=styles['Normal'],
        fontSize=10, fontName='Helvetica-Bold', textColor=colors.white,
        alignment=TA_LEFT, spaceBefore=0, spaceAfter=0,
        leftPadding=8, rightPadding=8, topPadding=4, bottomPadding=4)

    # ── SECCIÓN 1: No encontradas en el sistema ───────────────────────────────
    no_enc = resultado.get('no_encontradas', [])
    banner1 = Table([[Paragraph(
        f'❌  NO ENCONTRADAS EN EL SISTEMA — {len(no_enc)} serie(s)',
        STYLE_SEC
    )]], colWidths=[ANCHO_UTIL])
    banner1.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), ROJO),
        ('TOPPADDING',    (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(banner1)

    if no_enc:
        STYLE_MONO = ParagraphStyle('Mono', parent=styles['Normal'],
            fontSize=8, fontName='Helvetica', leading=11)
        aclaracion = Paragraph(
            'Estos números de serie están en el listado pero no coinciden con ninguna '
            'netbook registrada en el sistema. Verificar errores de tipeo o si deben registrarse.',
            ParagraphStyle('Acl', parent=styles['Normal'],
                fontSize=7, fontName='Helvetica', textColor=colors.grey)
        )
        story.append(aclaracion)
        story.append(Spacer(1, 0.15*cm))

        # Mostrar en filas de 6 columnas
        COL_SERIE = 6
        filas_series = []
        fila_actual  = []
        for i, serie in enumerate(no_enc):
            fila_actual.append(serie)
            if len(fila_actual) == COL_SERIE:
                filas_series.append(fila_actual)
                fila_actual = []
        if fila_actual:
            while len(fila_actual) < COL_SERIE:
                fila_actual.append('')
            filas_series.append(fila_actual)

        col_w = [ANCHO_UTIL / COL_SERIE] * COL_SERIE
        t_series = Table(filas_series, colWidths=col_w)
        t_series.setStyle(TableStyle([
            ('FONTNAME',      (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE',      (0, 0), (-1, -1), 8),
            ('ROWBACKGROUNDS',(0, 0), (-1, -1), [colors.HexColor('#fff5f5'), colors.white]),
            ('GRID',          (0, 0), (-1, -1), 0.3, colors.HexColor('#fca5a5')),
            ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING',    (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(t_series)
    else:
        story.append(Paragraph(
            'Todas las series del listado fueron encontradas en el sistema. ✅',
            ParagraphStyle('Ok', parent=styles['Normal'],
                fontSize=9, fontName='Helvetica', textColor=VERDE)
        ))

    story.append(Spacer(1, 0.5*cm))

    # ── SECCIÓN 2: En el sistema pero ausentes del listado ────────────────────
    no_list = resultado.get('no_en_listado', [])
    banner2 = Table([[Paragraph(
        f'⚠️  EN EL SISTEMA PERO AUSENTES DEL LISTADO — {len(no_list)} netbook(s)',
        STYLE_SEC
    )]], colWidths=[ANCHO_UTIL])
    banner2.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), NARANJA),
        ('TOPPADDING',    (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(banner2)

    if no_list:
        HDR_NL = ['Carro', 'Aula', 'N° Interno', 'N° Serie', 'Alumno', 'Estado']
        data_nl = [HDR_NL]
        for nb in no_list:
            estado = 'Operativa' if nb['estado'] == 'operativa' else 'Serv. Técnico'
            data_nl.append([
                nb['carro'], nb['aula'], nb['numero_interno'],
                nb['numero_serie'], nb['alumno'], estado
            ])
        col_nl = [3*cm, 2.5*cm, 2.5*cm, 5.5*cm, 7*cm, 3.7*cm]
        t_nl = Table(data_nl, colWidths=col_nl)
        estilo_nl = _tabla_estilo(NARANJA)
        t_nl.setStyle(estilo_nl)
        story.append(t_nl)
    else:
        story.append(Paragraph(
            'No hay netbooks del sistema ausentes del listado.',
            ParagraphStyle('Ok2', parent=styles['Normal'],
                fontSize=9, fontName='Helvetica', textColor=colors.grey)
        ))

    story.append(Spacer(1, 0.5*cm))

    # ── SECCIÓN 3: Encontradas ─────────────────────────────────────────────────
    enc = resultado.get('encontradas', [])
    banner3 = Table([[Paragraph(
        f'✅  ENCONTRADAS EN EL SISTEMA — {len(enc)} netbook(s)',
        STYLE_SEC
    )]], colWidths=[ANCHO_UTIL])
    banner3.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), VERDE),
        ('TOPPADDING',    (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(banner3)

    if enc:
        HDR_E = ['Carro', 'Aula', 'N° Interno', 'N° Serie', 'Alumno', 'Estado']
        data_e = [HDR_E]
        for nb in enc:
            estado = 'Operativa' if nb['estado'] == 'operativa' else 'Serv. Técnico'
            data_e.append([
                nb['carro'], nb['aula'], nb['numero_interno'],
                nb['numero_serie'], nb['alumno'], estado
            ])
        col_e = [3*cm, 2.5*cm, 2.5*cm, 5.5*cm, 7*cm, 3.7*cm]
        t_e = Table(data_e, colWidths=col_e)
        t_e.setStyle(_tabla_estilo(VERDE))
        story.append(t_e)
    else:
        story.append(Paragraph(
            'No se encontraron coincidencias.',
            ParagraphStyle('Ok3', parent=styles['Normal'],
                fontSize=9, fontName='Helvetica', textColor=colors.grey)
        ))

    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph(
        f'SIGA-Tec — E.T. N°7 D.E. 5  ·  Control generado el '
        f'{resultado["fecha"]} por {resultado["usuario"]}',
        STYLE_FECHA
    ))

    doc.build(story)
    nombre = f'control_masivo_stock_{datetime.utcnow().strftime("%Y%m%d_%H%M")}.pdf'
    return _generar_response(buffer, nombre)


# ═════════════════════════════════════════════════════════════════════════════
#  INVENTARIO INTEGRAL DE NETBOOKS  (sesión 16)
#  Todas las netbooks del sistema: carros + asignaciones internas.
#  PDF landscape A4 con resumen por estado y tabla completa.
# ═════════════════════════════════════════════════════════════════════════════

def pdf_inventario_integral_netbooks():
    """
    PDF landscape con todas las netbooks del sistema:
      - Sección 1: Netbooks en carros (operativas, servicio, baja)
      - Sección 2: Asignaciones Internas activas
    Devuelve una Response de Flask (send_file).
    """
    from reportlab.lib.pagesizes import landscape
    from models import Netbook, Carro, AsignacionInterna, Docente

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4),
                            rightMargin=1.5*cm, leftMargin=1.5*cm,
                            topMargin=1.5*cm, bottomMargin=1.5*cm)
    story = []

    fecha_str = (datetime.utcnow() + ARG_OFFSET).strftime('%d/%m/%Y %H:%M')
    _encabezado(story, 'Inventario Integral de Netbooks',
                f'Generado el {fecha_str}')

    # ── Consultas ────────────────────────────────────────────────────────────
    netbooks = (Netbook.query
                .join(Carro)
                .order_by(Carro.numero_fisico, Netbook.numero_interno)
                .all())
    asignaciones = (AsignacionInterna.query
                    .filter_by(activa=True)
                    .order_by(AsignacionInterna.id)
                    .all())

    total_nb         = len(netbooks)
    total_operativas = sum(1 for n in netbooks if n.estado == 'operativa')
    total_servicio   = sum(1 for n in netbooks if n.estado == 'servicio_tecnico')
    total_baja       = sum(1 for n in netbooks if n.estado not in ('operativa', 'servicio_tecnico'))
    total_asig       = len(asignaciones)
    total_general    = total_nb + total_asig

    # ── Resumen ──────────────────────────────────────────────────────────────
    STYLE_RESUMEN_HDR = ParagraphStyle('ResHdr', parent=styles['Normal'],
        fontSize=8, fontName='Helvetica-Bold', textColor=colors.white,
        alignment=TA_CENTER)
    STYLE_RESUMEN_VAL = ParagraphStyle('ResVal', parent=styles['Normal'],
        fontSize=13, fontName='Helvetica-Bold', textColor=AZUL_ESCUELA,
        alignment=TA_CENTER)
    STYLE_RESUMEN_LBL = ParagraphStyle('ResLbl', parent=styles['Normal'],
        fontSize=7, fontName='Helvetica', textColor=colors.grey,
        alignment=TA_CENTER)

    def _res_celda(valor, etiqueta):
        return [Paragraph(str(valor), STYLE_RESUMEN_VAL),
                Paragraph(etiqueta,   STYLE_RESUMEN_LBL)]

    resumen_data = [[
        _res_celda(total_general,    'TOTAL GENERAL'),
        _res_celda(total_nb,         'EN CARROS'),
        _res_celda(total_operativas, 'OPERATIVAS'),
        _res_celda(total_servicio,   'SERVICIO TÉC.'),
        _res_celda(total_baja,       'BAJA'),
        _res_celda(total_asig,       'ASIG. INTERNAS'),
    ]]
    t_res = Table(resumen_data, colWidths=[4*cm]*6)
    t_res.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), AZUL_CLARO),
        ('BOX',           (0, 0), (-1, -1), 0.8, AZUL_ESCUELA),
        ('INNERGRID',     (0, 0), (-1, -1), 0.5, colors.HexColor('#bfdbfe')),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING',    (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        # Destacar total general
        ('BACKGROUND',    (0, 0), (0, 0),   AZUL_ESCUELA),
        ('TEXTCOLOR',     (0, 0), (0, 0),   colors.white),
    ]))
    story.append(t_res)
    story.append(Spacer(1, 0.5*cm))

    # ── SECCIÓN 1: Netbooks en carros ────────────────────────────────────────
    story.append(Paragraph('NETBOOKS EN CARROS', STYLE_SECCION))
    story.append(Spacer(1, 0.2*cm))

    STYLE_CELL8 = ParagraphStyle('Cell8', parent=styles['Normal'],
        fontSize=8, fontName='Helvetica')
    STYLE_TH = ParagraphStyle('Th', parent=styles['Normal'],
        fontSize=8, fontName='Helvetica-Bold', textColor=colors.white,
        alignment=TA_CENTER)

    # Ancho útil landscape A4 con márgenes 1.5cm = ~247mm
    # 8 columnas: Carro(18) + División(28) + Aula(20) + N°Int(18) + N°Serie(50) +
    #             Alumno Mañana(38) + Alumno Tarde(38) + Estado(21) = 231mm ✓
    COLS_NB  = ['Carro', 'División', 'Aula', 'N° Int.', 'N° Serie',
                'Alumno Mañana', 'Alumno Tarde', 'Estado']
    WIDTHS_NB = [18, 28, 20, 18, 50, 38, 38, 21]  # mm — suma = 231mm

    from reportlab.lib.units import mm as _mm

    def _nombre_alumno(nb, turno):
        """Devuelve apellido, nombre del alumno o '—'."""
        alumno_obj = nb.alumno_manana if turno == 'M' else nb.alumno_tarde
        if alumno_obj:
            return f'{alumno_obj.apellido}, {alumno_obj.nombre}'
        # fallback campo legacy
        if turno == 'M' and nb.alumno:
            return nb.alumno
        return '—'

    def _estado_nb(nb):
        if nb.estado == 'operativa':
            return 'Operativa'
        if nb.estado == 'servicio_tecnico':
            return 'Serv. Téc.'
        return nb.estado.capitalize()

    header_nb = [Paragraph(c, STYLE_TH) for c in COLS_NB]
    data_nb   = [header_nb]
    estados_nb = []

    for nb in netbooks:
        carro = nb.carro
        data_nb.append([
            Paragraph(carro.display if carro else '—',     STYLE_CELL8),
            Paragraph(carro.division or '—' if carro else '—', STYLE_CELL8),
            Paragraph(carro.aula or '—' if carro else '—',     STYLE_CELL8),
            Paragraph(nb.numero_interno or '—',                STYLE_CELL8),
            Paragraph(nb.numero_serie or '—',                  STYLE_CELL8),
            Paragraph(_nombre_alumno(nb, 'M'),                 STYLE_CELL8),
            Paragraph(_nombre_alumno(nb, 'T'),                 STYLE_CELL8),
            Paragraph(_estado_nb(nb),                          STYLE_CELL8),
        ])
        estados_nb.append(nb.estado)

    if len(data_nb) > 1:
        ts_nb = [
            ('BACKGROUND',    (0, 0), (-1, 0),  AZUL_ESCUELA),
            ('ROWBACKGROUNDS',(0, 1), (-1, -1), [colors.white, GRIS_CLARO]),
            ('GRID',          (0, 0), (-1, -1), 0.4, colors.HexColor('#e5e7eb')),
            ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING',    (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING',   (0, 0), (-1, -1), 4),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 4),
        ]
        for i, estado in enumerate(estados_nb, start=1):
            if estado == 'servicio_tecnico':
                ts_nb += [('TEXTCOLOR', (7, i), (7, i), NARANJA),
                           ('FONTNAME',  (7, i), (7, i), 'Helvetica-Bold')]
            elif estado not in ('operativa', 'servicio_tecnico'):
                ts_nb += [('TEXTCOLOR', (7, i), (7, i), ROJO),
                           ('FONTNAME',  (7, i), (7, i), 'Helvetica-Bold')]

        t_nb = Table(data_nb, colWidths=[w * _mm for w in WIDTHS_NB], repeatRows=1)
        t_nb.setStyle(TableStyle(ts_nb))
        story.append(t_nb)
        story.append(Spacer(1, 0.3*cm))
        story.append(Paragraph(
            f'Total: {total_nb} netbook(s)  |  '
            f'Operativas: {total_operativas}  |  '
            f'Servicio técnico: {total_servicio}  |  '
            f'Baja: {total_baja}',
            STYLE_NORMAL
        ))
    else:
        story.append(Paragraph('No hay netbooks cargadas en el sistema.', STYLE_NORMAL))

    story.append(Spacer(1, 0.8*cm))
    story.append(HRFlowable(width='100%', thickness=1.5, color=VERDE))
    story.append(Spacer(1, 0.3*cm))

    # ── SECCIÓN 2: Asignaciones Internas ─────────────────────────────────────
    STYLE_SECCION_VERDE = ParagraphStyle('SeccionVerde', parent=styles['Normal'],
        fontSize=12, fontName='Helvetica-Bold',
        textColor=VERDE, spaceBefore=4, spaceAfter=4)

    story.append(Paragraph('ASIGNACIONES INTERNAS ACTIVAS', STYLE_SECCION_VERDE))
    story.append(Paragraph(
        'Netbooks asignadas permanentemente a docentes o áreas — no forman parte de ningún carro.',
        ParagraphStyle('SubAI', parent=styles['Normal'],
            fontSize=8, fontName='Helvetica', textColor=colors.grey, spaceAfter=6)
    ))
    story.append(Spacer(1, 0.2*cm))

    if asignaciones:
        # 6 columnas ajustadas para que el texto se lea bien
        # N°Int(20) + N°Serie(52) + Modelo(48) + Destinatario(62) + Motivo(48) + Fecha(20) = 250mm
        # Con márgenes 1.5cm ancho útil landscape = ~247mm — ajustamos a 247mm exacto
        # N°Int(19) + N°Serie(50) + Modelo(47) + Destinatario(62) + Motivo(48) + Fecha(21) = 247mm ✓
        COLS_AI   = ['N° Interno', 'N° Serie', 'Modelo', 'Destinatario / Área', 'Motivo', 'Fecha asig.']
        WIDTHS_AI = [19, 50, 47, 62, 48, 21]  # suma = 247mm

        STYLE_TH_VERDE = ParagraphStyle('ThVerde', parent=styles['Normal'],
            fontSize=8, fontName='Helvetica-Bold', textColor=colors.white,
            alignment=TA_CENTER)

        header_ai = [Paragraph(c, STYLE_TH_VERDE) for c in COLS_AI]
        data_ai   = [header_ai]

        for a in asignaciones:
            dest = a.destinatario
            fecha_asig = (a.fecha_asignacion + ARG_OFFSET).strftime('%d/%m/%Y') \
                         if a.fecha_asignacion else '—'
            data_ai.append([
                Paragraph(a.numero_interno or '—', STYLE_CELL8),
                Paragraph(a.numero_serie   or '—', STYLE_CELL8),
                Paragraph(a.modelo         or '—', STYLE_CELL8),
                Paragraph(dest,                    STYLE_CELL8),
                Paragraph(a.motivo         or '—', STYLE_CELL8),
                Paragraph(fecha_asig,              STYLE_CELL8),
            ])

        ts_ai = [
            ('BACKGROUND',    (0, 0), (-1, 0),  VERDE),
            ('ROWBACKGROUNDS',(0, 1), (-1, -1), [colors.white, colors.HexColor('#f0fdf4')]),
            ('GRID',          (0, 0), (-1, -1), 0.4, colors.HexColor('#d1fae5')),
            ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING',    (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING',   (0, 0), (-1, -1), 5),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 5),
        ]
        t_ai = Table(data_ai, colWidths=[w * _mm for w in WIDTHS_AI], repeatRows=1)
        t_ai.setStyle(TableStyle(ts_ai))
        story.append(t_ai)
        story.append(Spacer(1, 0.3*cm))
        story.append(Paragraph(
            f'Total asignaciones internas activas: {total_asig}',
            STYLE_NORMAL
        ))
    else:
        story.append(Paragraph('No hay asignaciones internas activas registradas.', STYLE_NORMAL))

    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph(
        f'SIGA-Tec — E.T. N°7 D.E. 5  ·  Inventario generado el {fecha_str}',
        STYLE_FECHA
    ))

    doc.build(story)
    nombre = f'inventario_integral_netbooks_{datetime.utcnow().strftime("%Y%m%d_%H%M")}.pdf'
    return _generar_response(buffer, nombre)


# ═════════════════════════════════════════════════════════════════════════════
#  MÓDULO TVs — Etiquetas y Historial  (sesión 14 — corregido anchos PDF)
# ═════════════════════════════════════════════════════════════════════════════

from reportlab.lib.pagesizes import landscape
from reportlab.lib.units import mm

_AZUL_TV    = colors.HexColor('#1a2a6c')
_NARANJA_TV = colors.HexColor('#e8821a')
_VERDE_TV   = colors.HexColor('#198754')
_GRIS_TV    = colors.HexColor('#f5f5f5')


def _st_tv():
    return {
        'titulo': ParagraphStyle('tv_titulo', fontName='Helvetica-Bold', fontSize=13,
                                 textColor=AZUL_ESCUELA, alignment=TA_CENTER, leading=16),
        'sub':    ParagraphStyle('tv_sub',    fontName='Helvetica', fontSize=8,
                                 textColor=colors.grey, alignment=TA_CENTER),
        'th':     ParagraphStyle('tv_th',     fontName='Helvetica-Bold', fontSize=7,
                                 textColor=colors.white, alignment=TA_CENTER),
        'td':     ParagraphStyle('tv_td',     fontName='Helvetica', fontSize=7,
                                 alignment=TA_LEFT, leading=9),
        'tdc':    ParagraphStyle('tv_tdc',    fontName='Helvetica', fontSize=7,
                                 alignment=TA_CENTER, leading=9),
        'et':     ParagraphStyle('tv_et',     fontName='Helvetica-Bold', fontSize=8.5,
                                 textColor=colors.white, alignment=TA_CENTER),
        'em':     ParagraphStyle('tv_em',     fontName='Helvetica', fontSize=8,
                                 alignment=TA_CENTER, leading=11),
        'es':     ParagraphStyle('tv_es',     fontName='Helvetica', fontSize=6.5,
                                 textColor=colors.grey, alignment=TA_CENTER),
    }


def pdf_historial_tvs(prestamos):
    """
    PDF landscape historial de préstamos de TVs.
    Devuelve bytes.
    Anchos ajustados para que no desborden en A4 landscape (útil ~247mm).
    """
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4),
                            topMargin=1.5*cm, bottomMargin=1.5*cm,
                            leftMargin=1.5*cm, rightMargin=1.5*cm)
    st    = _st_tv()
    story = []
    _encabezado(story, 'Historial de Préstamos — Televisores')

    # Ancho útil landscape A4 con márgenes 1.5cm = 297 - 3 = 247mm
    # 9 columnas — deben sumar ≤ 247mm
    COLS   = ['TV', 'Solicitante', 'Aula destino', 'Retiro',
              'Dev. esperada', 'Dev. real', 'Autorizó retiro', 'Autorizó dev.', 'Estado']
    WIDTHS = [18, 48, 32, 34, 34, 34, 38, 38, 22]  # suma = 298mm / 10 = ~247mm útil

    def _fmt(dt):
        return _arg_full(dt)

    def _nom(p):
        if p.docente:
            return f'{p.docente.apellido}, {p.docente.nombre}'
        return p.nombre_solicitante or '—'

    def _enc(u):
        return f'{u.apellido} {u.nombre}' if u else '—'

    header = [Paragraph(c, st['th']) for c in COLS]
    data   = [header]
    for p in prestamos:
        data.append([
            Paragraph(p.tv.codigo if p.tv else '—',  st['tdc']),
            Paragraph(_nom(p),                        st['td']),
            Paragraph(p.aula_destino or '—',          st['tdc']),
            Paragraph(_fmt(p.fecha_retiro),            st['tdc']),
            Paragraph(_fmt(p.fecha_devolucion_esperada), st['tdc']),
            Paragraph(_fmt(p.fecha_devolucion_real),   st['tdc']),
            Paragraph(_enc(p.encargado_retiro),        st['td']),
            Paragraph(_enc(p.encargado_devolucion),    st['td']),
            Paragraph(p.estado.upper(),                st['tdc']),
        ])

    ts = [
        ('BACKGROUND',    (0, 0), (-1, 0),  _AZUL_TV),
        ('ROWBACKGROUNDS',(0, 1), (-1, -1), [colors.white, _GRIS_TV]),
        ('GRID',          (0, 0), (-1, -1), 0.4, colors.lightgrey),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING',    (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]
    for i, p in enumerate(prestamos, start=1):
        c = _VERDE_TV if p.estado == 'devuelto' else _NARANJA_TV
        ts += [('TEXTCOLOR', (8, i), (8, i), c),
               ('FONTNAME',  (8, i), (8, i), 'Helvetica-Bold')]

    t = Table(data, colWidths=[w * mm for w in WIDTHS], repeatRows=1)
    t.setStyle(TableStyle(ts))
    story.append(t)
    doc.build(story)
    return buf.getvalue()


def pdf_etiquetas_tvs(tvs):
    """
    PDF A4 etiquetas de TVs, 2 columnas × N filas, 88×56mm.
    Devuelve bytes.
    """
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            topMargin=10*mm, bottomMargin=10*mm,
                            leftMargin=10*mm, rightMargin=10*mm)
    st    = _st_tv()
    story = []
    _encabezado(story, 'Etiquetas — Televisores')

    W = 88*mm; H = 56*mm; COLS = 2
    celdas = []
    for tv in tvs:
        comp  = ', '.join(tv.componentes_lista) if tv.componentes_lista else 'Sin accesorios'
        celdas.append(_armar_etiqueta_tv(
            color=_AZUL_TV, tipo_txt='TELEVISOR', codigo=tv.codigo,
            linea1=f'{tv.marca} {tv.modelo}' + (f'  {tv.pulgadas}"' if tv.pulgadas else ''),
            linea2=f'Aula: {tv.aula or "—"}',
            linea3=f'N° serie: {tv.numero_serie or "—"}',
            detalle=comp, st=st, W=W,
        ))

    if celdas:
        story.append(_grid_etiquetas_tv(celdas, W, H, COLS))
    doc.build(story)
    return buf.getvalue()


def _armar_etiqueta_tv(color, tipo_txt, codigo, linea1, linea2, linea3, detalle, st, W):
    celda = [
        Table([[Paragraph(f'<b>{tipo_txt}</b>  ·  {codigo}', st['et'])]],
              colWidths=[W - 6],
              style=[('BACKGROUND', (0,0), (-1,-1), color),
                     ('TOPPADDING', (0,0), (-1,-1), 4),
                     ('BOTTOMPADDING', (0,0), (-1,-1), 4)]),
        Spacer(1, 1.5*mm),
    ]
    if linea1: celda.append(Paragraph(f'<b>{linea1}</b>', st['em']))
    if linea2: celda.append(Paragraph(linea2, st['em']))
    if linea3: celda.append(Paragraph(linea3, st['es']))
    if detalle:
        celda.append(HRFlowable(width=W - 12, thickness=0.5, color=colors.lightgrey))
        celda.append(Paragraph(f'<i>{detalle}</i>', st['es']))
    return celda


def _grid_etiquetas_tv(celdas, W, H, COLS):
    filas = []
    fila  = []
    for celda in celdas:
        fila.append(celda)
        if len(fila) == COLS:
            filas.append(fila); fila = []
    if fila:
        while len(fila) < COLS: fila.append('')
        filas.append(fila)
    t = Table(filas, colWidths=[W]*COLS, rowHeights=[H]*len(filas))
    t.setStyle(TableStyle([
        ('BOX',         (0,0), (-1,-1), 0.8, colors.grey),
        ('INNERGRID',   (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('VALIGN',      (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING',  (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 3),
        ('RIGHTPADDING',(0,0), (-1,-1), 3),
    ]))
    return t
