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
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                             rightMargin=1.5*cm, leftMargin=1.5*cm,
                             topMargin=1.5*cm, bottomMargin=1.5*cm)
    story = []
    _encabezado(story, 'Historial de Préstamos — Carros',
                f'Período: {periodo.capitalize()}')

    data = [['Código', 'Docente', 'Carro', 'Retiro', 'Devolución', 'Duración', 'Estado']]
    for p in prestamos:
        dur = '—'
        if p.duracion_minutos:
            dur = f'{p.duracion_minutos//60}h {p.duracion_minutos%60}m'
        elif p.hora_devolucion and p.hora_retiro:
            diff = int((p.hora_devolucion - p.hora_retiro).total_seconds() // 60)
            dur = f'{diff//60}h {diff%60}m'
        nombre_docente = ''
        if p.docente:
            nombre_docente = f'{p.docente.apellido}, {p.docente.nombre}' if hasattr(p.docente, 'apellido') else (p.docente.nombre_completo if hasattr(p.docente, 'nombre_completo') else str(p.docente))
        data.append([
            p.codigo or '—',
            Paragraph(nombre_docente, STYLE_NORMAL),
            p.carro.display if p.carro else '—',
            _arg(p.hora_retiro),
            _arg(p.hora_devolucion) if p.hora_devolucion else '—',
            dur,
            'Activo' if p.estado == 'activo' else 'Devuelto'
        ])

    if len(data) > 1:
        t = Table(data, colWidths=[1.6*cm, 5.5*cm, 1.6*cm, 2.7*cm, 2.7*cm, 1.8*cm, 2.1*cm])
        estilo = _tabla_estilo()
        for i, p in enumerate(prestamos, start=1):
            if p.estado == 'activo':
                estilo.add('TEXTCOLOR', (6, i), (6, i), NARANJA)
                estilo.add('FONTNAME',  (6, i), (6, i), 'Helvetica-Bold')
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
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                             rightMargin=1.5*cm, leftMargin=1.5*cm,
                             topMargin=1.5*cm, bottomMargin=1.5*cm)
    story = []
    _encabezado(story, 'Historial de Préstamos — Espacio Digital',
                f'Período: {periodo.capitalize()}')

    STYLE_DETALLE = ParagraphStyle('Detalle', parent=styles['Normal'],
        fontSize=7, fontName='Helvetica', textColor=colors.HexColor('#374151'))
    STYLE_NB = ParagraphStyle('NB', parent=styles['Normal'],
        fontSize=7, fontName='Helvetica-Bold', textColor=AZUL_ESCUELA)

    # Cabecera principal
    data = [['Código', 'Docente', 'Netbooks', 'Retiro', 'Devolución', 'Autorizado por', 'Estado']]
    row_estados = []

    for p in prestamos:
        nombre_docente = ''
        if p.docente:
            nombre_docente = f'{p.docente.apellido}, {p.docente.nombre}' if hasattr(p.docente, 'apellido') else str(p.docente)

        # Armar celda de netbooks: "N°12 — Apellido, Nombre" por línea
        if p.items:
            lineas = []
            for item in p.items:
                linea = f'N°{item.numero_interno}'
                if item.alumno:
                    linea += f' — {item.alumno}'
                lineas.append(linea)
            nb_cell = Paragraph('\n'.join(lineas), STYLE_NB)
        else:
            nb_cell = Paragraph('—', STYLE_DETALLE)

        data.append([
            p.codigo or '—',
            Paragraph(nombre_docente, STYLE_NORMAL),
            nb_cell,
            _arg(p.hora_retiro),
            _arg(p.hora_devolucion) if p.hora_devolucion else '—',
            Paragraph(p.encargado_retiro or '—', STYLE_DETALLE),
            'Activo' if p.estado == 'activo' else 'Devuelto'
        ])
        row_estados.append(p.estado)

    if len(data) > 1:
        t = Table(data, colWidths=[1.6*cm, 4.5*cm, 3.8*cm, 2.5*cm, 2.5*cm, 3.5*cm, 1.6*cm])
        estilo = _tabla_estilo(colors.HexColor('#1d4ed8'))
        # Alinear columna Netbooks a la izquierda
        estilo.add('ALIGN', (2, 0), (2, -1), 'LEFT')
        for i, estado in enumerate(row_estados, start=1):
            if estado == 'activo':
                estilo.add('TEXTCOLOR', (6, i), (6, i), NARANJA)
                estilo.add('FONTNAME',  (6, i), (6, i), 'Helvetica-Bold')
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
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                             rightMargin=1.5*cm, leftMargin=1.5*cm,
                             topMargin=1.5*cm, bottomMargin=1.5*cm)
    story = []
    _encabezado(story, 'Estadísticas de Uso del Sistema')

    story.append(Paragraph('Top Docentes por Préstamos', STYLE_SECCION))
    data = [['#', 'Docente', 'Materia', 'Total Préstamos']]
    for i, (docente, total) in enumerate(top_docentes, start=1):
        data.append([str(i), docente.nombre_completo, docente.materia or '—', str(total)])

    if len(data) > 1:
        t = Table(data, colWidths=[1*cm, 7*cm, 6*cm, 3.5*cm])
        t.setStyle(_tabla_estilo())
        story.append(t)
    else:
        story.append(Paragraph('Sin datos.', STYLE_NORMAL))

    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph('Top Materias por Préstamos', STYLE_SECCION))
    data2 = [['#', 'Materia', 'Total Préstamos']]
    for i, (materia, total) in enumerate(top_materias, start=1):
        data2.append([str(i), materia or 'Sin materia', str(total)])

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
