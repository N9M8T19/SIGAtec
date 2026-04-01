"""
services/pdf_stock.py
PDF de informe de control de stock de netbooks.
"""

import os
from io import BytesIO
from datetime import datetime

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

AZUL_ESCUELA = colors.HexColor('#1e3a8a')
AZUL_CLARO   = colors.HexColor('#dbeafe')
GRIS_CLARO   = colors.HexColor('#f3f4f6')
VERDE        = colors.HexColor('#16a34a')
ROJO         = colors.HexColor('#dc2626')
NARANJA      = colors.HexColor('#f97316')
VERDE_CLARO  = colors.HexColor('#dcfce7')
ROJO_CLARO   = colors.HexColor('#fee2e2')
NARANJA_CLARO= colors.HexColor('#ffedd5')

styles = getSampleStyleSheet()

STYLE_TITULO = ParagraphStyle('Titulo', parent=styles['Normal'],
    fontSize=16, fontName='Helvetica-Bold',
    textColor=AZUL_ESCUELA, alignment=TA_CENTER, spaceAfter=4)
STYLE_SUBTITULO = ParagraphStyle('Subtitulo', parent=styles['Normal'],
    fontSize=10, fontName='Helvetica',
    textColor=colors.grey, alignment=TA_CENTER, spaceAfter=2)
STYLE_SECCION = ParagraphStyle('Seccion', parent=styles['Normal'],
    fontSize=11, fontName='Helvetica-Bold',
    textColor=AZUL_ESCUELA, spaceBefore=8, spaceAfter=4)
STYLE_NORMAL = ParagraphStyle('Normal2', parent=styles['Normal'],
    fontSize=9, fontName='Helvetica')
STYLE_FECHA = ParagraphStyle('Fecha', parent=styles['Normal'],
    fontSize=8, fontName='Helvetica',
    textColor=colors.grey, alignment=TA_RIGHT)


def _encabezado(story, titulo, subtitulo=''):
    logo_path = os.path.join('static', 'img', 'logo_escuela.png')
    fecha_str = datetime.now().strftime('%d/%m/%Y %H:%M')

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


def pdf_control_stock(carro, resultado):
    """Genera el PDF del informe de control de stock."""
    buffer = BytesIO()
    doc    = SimpleDocTemplate(buffer, pagesize=A4,
                                rightMargin=1.5*cm, leftMargin=1.5*cm,
                                topMargin=1.5*cm, bottomMargin=1.5*cm)
    story  = []

    _encabezado(story, f'Control de Stock — Carro {carro.display}',
                f'Relevamiento realizado el {resultado["fecha"]} por {resultado["usuario"]}')

    # ── Resumen ejecutivo ─────────────────────────────────────────────────────
    story.append(Spacer(1, 0.3*cm))

    total_s   = resultado['total_sistema']
    total_e   = resultado['total_escaneadas']
    encontr   = resultado['encontradas']
    n_falt    = len(resultado['faltantes'])
    n_extra   = len(resultado['no_registradas'])

    resumen_data = [
        ['En el sistema', 'Escaneadas', 'Encontradas', 'Faltantes', 'No registradas'],
        [str(total_s), str(total_e), str(encontr), str(n_falt), str(n_extra)]
    ]
    t_res = Table(resumen_data, colWidths=[3.5*cm]*5)
    t_res.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0),  AZUL_CLARO),
        ('TEXTCOLOR',     (0, 0), (-1, 0),  AZUL_ESCUELA),
        ('FONTNAME',      (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, -1), 10),
        ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
        ('GRID',          (0, 0), (-1, -1), 0.5, colors.HexColor('#93c5fd')),
        ('TOPPADDING',    (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        # Colorear faltantes en rojo
        ('BACKGROUND',    (3, 1), (3, 1),  ROJO_CLARO if n_falt > 0 else VERDE_CLARO),
        ('TEXTCOLOR',     (3, 1), (3, 1),  ROJO if n_falt > 0 else VERDE),
        # Colorear no registradas en naranja
        ('BACKGROUND',    (4, 1), (4, 1),  NARANJA_CLARO if n_extra > 0 else VERDE_CLARO),
        ('TEXTCOLOR',     (4, 1), (4, 1),  NARANJA if n_extra > 0 else VERDE),
    ]))
    story.append(t_res)
    story.append(Spacer(1, 0.5*cm))

    # ── Netbooks faltantes ────────────────────────────────────────────────────
    if resultado['faltantes']:
        story.append(Paragraph(f'❌ Netbooks Faltantes ({n_falt})', STYLE_SECCION))
        data = [['N° Interno', 'N° Serie', 'Alumno Asignado', 'Estado en sistema']]
        for nb in resultado['faltantes']:
            estado = 'Operativa' if nb['estado'] == 'operativa' else 'Servicio Técnico'
            data.append([nb['numero_interno'], nb['numero_serie'], nb['alumno'], estado])

        t = Table(data, colWidths=[3*cm, 5.5*cm, 6*cm, 4*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, 0),  ROJO),
            ('TEXTCOLOR',     (0, 0), (-1, 0),  colors.white),
            ('FONTNAME',      (0, 0), (-1, 0),  'Helvetica-Bold'),
            ('FONTSIZE',      (0, 0), (-1, -1), 8),
            ('FONTNAME',      (0, 1), (-1, -1), 'Helvetica'),
            ('ROWBACKGROUNDS',(0, 1), (-1, -1), [colors.white, ROJO_CLARO]),
            ('GRID',          (0, 0), (-1, -1), 0.5, colors.HexColor('#fca5a5')),
            ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING',    (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING',   (0, 0), (-1, -1), 6),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 6),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.4*cm))
    else:
        story.append(Paragraph('✅ No hay netbooks faltantes.', STYLE_NORMAL))
        story.append(Spacer(1, 0.3*cm))

    # ── Netbooks no registradas ───────────────────────────────────────────────
    if resultado['no_registradas']:
        story.append(Paragraph(f'⚠️ Escaneadas pero NO registradas en el sistema ({n_extra})',
                                STYLE_SECCION))
        data2 = [['N° Serie escaneada']]
        for serie in resultado['no_registradas']:
            data2.append([serie])

        t2 = Table(data2, colWidths=[18.5*cm])
        t2.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, 0),  NARANJA),
            ('TEXTCOLOR',     (0, 0), (-1, 0),  colors.white),
            ('FONTNAME',      (0, 0), (-1, 0),  'Helvetica-Bold'),
            ('FONTSIZE',      (0, 0), (-1, -1), 8),
            ('FONTNAME',      (0, 1), (-1, -1), 'Helvetica'),
            ('ROWBACKGROUNDS',(0, 1), (-1, -1), [colors.white, NARANJA_CLARO]),
            ('GRID',          (0, 0), (-1, -1), 0.5, colors.HexColor('#fdba74')),
            ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING',    (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING',   (0, 0), (-1, -1), 6),
        ]))
        story.append(t2)
        story.append(Spacer(1, 0.4*cm))

    # ── Firma ─────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 1*cm))
    story.append(HRFlowable(width='100%', thickness=0.5, color=colors.HexColor('#e5e7eb')))
    story.append(Spacer(1, 0.5*cm))
    firma_data = [[
        Paragraph('_________________________\nEncargado/a que realizó el relevamiento', STYLE_NORMAL),
        Paragraph('_________________________\nDirectivo/a', STYLE_NORMAL),
        Paragraph('_________________________\nFecha y hora', STYLE_NORMAL),
    ]]
    t_firma = Table(firma_data, colWidths=[6*cm, 6*cm, 6*cm])
    t_firma.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER')]))
    story.append(t_firma)

    doc.build(story)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True,
                     download_name=f'stock_carro_{carro.numero_fisico}.pdf',
                     mimetype='application/pdf')
