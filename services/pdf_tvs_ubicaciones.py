# ══════════════════════════════════════════════════════════════════════════════
# AGREGAR AL FINAL DE services/pdf_reportes.py
# ══════════════════════════════════════════════════════════════════════════════
#
# Los imports de reportlab ya deben estar al inicio del archivo.
# Solo agregar si no existen:
#
#   from reportlab.lib.pagesizes import A4, landscape
#   from reportlab.lib import colors
#   from reportlab.lib.units import mm
#   from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
#                                   Paragraph, Spacer, HRFlowable, Image as RLImage)
#   from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
#   from reportlab.lib.enums import TA_CENTER, TA_LEFT
#   import os, io
#
# ARG_OFFSET ya está definido en el archivo como timedelta(hours=-3).
# LOGO_PATH ya está definido como la ruta a static/img/logo_escuela.png.
# Las funciones _header_pdf() o equivalente ya existen — usar la del proyecto.
# ══════════════════════════════════════════════════════════════════════════════

# ─ Colores institucionales (consistentes con el resto del archivo) ────────────
_AZUL    = colors.HexColor('#1a2a6c')
_NARANJA = colors.HexColor('#e8821a')
_VERDE   = colors.HexColor('#198754')
_BLANCO  = colors.white
_GRIS    = colors.HexColor('#f5f5f5')


def _st():
    """Estilos reutilizables para estas funciones."""
    return {
        'title': ParagraphStyle('tvtitle', fontName='Helvetica-Bold', fontSize=13,
                                textColor=_AZUL, alignment=TA_CENTER, leading=16),
        'sub':   ParagraphStyle('tvsub',   fontName='Helvetica', fontSize=8,
                                textColor=colors.grey, alignment=TA_CENTER),
        'th':    ParagraphStyle('tvth',    fontName='Helvetica-Bold', fontSize=8,
                                textColor=_BLANCO, alignment=TA_CENTER),
        'td':    ParagraphStyle('tvtd',    fontName='Helvetica', fontSize=8,
                                alignment=TA_LEFT,   leading=10),
        'tdc':   ParagraphStyle('tvtdc',   fontName='Helvetica', fontSize=8,
                                alignment=TA_CENTER, leading=10),
        'en':    ParagraphStyle('tven',    fontName='Helvetica-Bold', fontSize=16,
                                textColor=_AZUL, alignment=TA_CENTER),
        'em':    ParagraphStyle('tvem',    fontName='Helvetica', fontSize=8,
                                alignment=TA_CENTER, leading=11),
        'es':    ParagraphStyle('tves',    fontName='Helvetica', fontSize=6.5,
                                textColor=colors.grey, alignment=TA_CENTER),
        'et':    ParagraphStyle('tvet',    fontName='Helvetica-Bold', fontSize=8.5,
                                textColor=_BLANCO, alignment=TA_CENTER),
    }


def _encabezado_pdf(story, titulo, st):
    """Encabezado estándar: logo + título + fecha."""
    ahora = (datetime.utcnow() + ARG_OFFSET).strftime('%d/%m/%Y %H:%M')
    logo  = RLImage(LOGO_PATH, 13*mm, 13*mm) if os.path.exists(LOGO_PATH) else ''
    fila  = [[logo,
              Paragraph(f'E.T. N°7 D.E. 5 — Dolores Lavalle de Lavalle<br/>'
                        f'<font size="12"><b>{titulo}</b></font>', st['title']),
              Paragraph(ahora, st['sub'])]]
    t = Table(fila, colWidths=['12%', '76%', '12%'])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), _GRIS),
        ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
        ('TOPPADDING',    (0,0),(-1,-1), 5),
        ('BOTTOMPADDING', (0,0),(-1,-1), 5),
    ]))
    story.append(t)
    story.append(Spacer(1, 5*mm))


# ─────────────────────────────────────────────────────────────────────────────
# ETIQUETAS — TVs
# Formato A4, 2 columnas × N filas, 88 × 56 mm por etiqueta.
# ─────────────────────────────────────────────────────────────────────────────

def pdf_etiquetas_tvs(tvs):
    """
    Genera un PDF A4 con etiquetas para los televisores.
    Cada etiqueta muestra: código, marca/modelo, pulgadas,
    aula, N° de serie y componentes incluidos.
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            topMargin=10*mm, bottomMargin=10*mm,
                            leftMargin=10*mm, rightMargin=10*mm)
    st    = _st()
    story = []
    _encabezado_pdf(story, 'ETIQUETAS — TELEVISORES', st)

    W = 88*mm   # ancho etiqueta
    H = 56*mm   # alto etiqueta
    COLS = 2

    celdas = []
    for tv in tvs:
        comp = ', '.join(tv.componentes_lista) if tv.componentes_lista else 'Sin accesorios'
        aula = tv.aula or '—'
        serie = tv.numero_serie or '—'
        pulg  = f'  {tv.pulgadas}"' if tv.pulgadas else ''

        celda = _armar_etiqueta(
            color     = _AZUL,
            tipo_txt  = 'TELEVISOR',
            codigo    = tv.codigo,
            linea1    = f'{tv.marca} {tv.modelo}{pulg}',
            linea2    = f'Aula: {aula}',
            linea3    = f'N° serie: {serie}',
            detalle   = comp,
            st        = st,
            W         = W,
        )
        celdas.append(celda)

    story.append(_grid_etiquetas(celdas, W, H, COLS))
    doc.build(story)
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# HISTORIAL DE PRÉSTAMOS — TVs  (landscape)
# ─────────────────────────────────────────────────────────────────────────────

def pdf_historial_tvs(prestamos):
    """PDF landscape con el historial completo de préstamos de TVs."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4),
                            topMargin=10*mm, bottomMargin=10*mm,
                            leftMargin=12*mm, rightMargin=12*mm)
    st    = _st()
    story = []
    _encabezado_pdf(story, 'HISTORIAL DE PRÉSTAMOS — TELEVISORES', st)

    COLS   = ['TV', 'Solicitante', 'Aula destino', 'Retiro',
              'Dev. esperada', 'Dev. real', 'Autorizó retiro', 'Autorizó dev.', 'Estado']
    WIDTHS = [30, 62, 45, 48, 48, 48, 50, 50, 36]  # mm, total ≈ 417 mm (A4 landscape ≈ 267mm útil — ajustar si necesario)

    def _fmt(dt):
        return (dt + ARG_OFFSET).strftime('%d/%m/%Y %H:%M') if dt else '—'

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
            Paragraph(p.tv.codigo if p.tv else '—', st['tdc']),
            Paragraph(_nom(p),                       st['td']),
            Paragraph(p.aula_destino or '—',         st['tdc']),
            Paragraph(_fmt(p.fecha_retiro),           st['tdc']),
            Paragraph(_fmt(p.fecha_devolucion_esperada), st['tdc']),
            Paragraph(_fmt(p.fecha_devolucion_real),  st['tdc']),
            Paragraph(_enc(p.encargado_retiro),       st['td']),
            Paragraph(_enc(p.encargado_devolucion),   st['td']),
            Paragraph(p.estado.upper(),               st['tdc']),
        ])

    ts = [
        ('BACKGROUND',    (0, 0), (-1, 0),  _AZUL),
        ('ROWBACKGROUNDS',(0, 1), (-1, -1), [_BLANCO, _GRIS]),
        ('GRID',          (0, 0), (-1, -1), 0.4, colors.lightgrey),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING',    (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]
    for i, p in enumerate(prestamos, start=1):
        color = _VERDE if p.estado == 'devuelto' else _NARANJA
        ts += [('TEXTCOLOR', (8,i),(8,i), color),
               ('FONTNAME',  (8,i),(8,i), 'Helvetica-Bold')]

    t = Table(data, colWidths=[w*mm for w in WIDTHS], repeatRows=1)
    t.setStyle(TableStyle(ts))
    story.append(t)
    doc.build(story)
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# ETIQUETAS UNIFICADAS — TVs + Pantallas Digitales + Impresoras 3D
# Una etiqueta por equipo con ubicación activa registrada.
# Colores: TV=azul, Pantalla=verde, Impresora=naranja
# ─────────────────────────────────────────────────────────────────────────────

def pdf_etiquetas_equipos(tvs_data, pantallas_data, impresoras_data):
    """
    PDF A4, 2 columnas, etiquetas 88×56 mm para todos los equipos con
    ubicación fija registrada.

    tvs_data        → lista de {'equipo': TV, 'ubic': UbicacionEquipo}
    pantallas_data  → lista de {'equipo': PantallaDigital, 'ubic': UbicacionEquipo}
    impresoras_data → lista de {'equipo': Impresora3D, 'ubic': UbicacionEquipo}
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            topMargin=10*mm, bottomMargin=10*mm,
                            leftMargin=10*mm, rightMargin=10*mm)
    st    = _st()
    story = []
    _encabezado_pdf(story, 'ETIQUETAS — EQUIPOS TECNOLÓGICOS', st)

    W    = 88*mm
    H    = 56*mm
    COLS = 2

    celdas = []

    # ── TVs ──────────────────────────────────────────────────────────────────
    for item in tvs_data:
        tv, ubic = item['equipo'], item['ubic']
        comp  = ', '.join(tv.componentes_lista) if tv.componentes_lista else 'Sin accesorios'
        pulg  = f'  {tv.pulgadas}"' if tv.pulgadas else ''
        aula  = ubic.aula + (f' — {ubic.sector}' if ubic.sector else '')
        celdas.append(_armar_etiqueta(
            color    = _AZUL,
            tipo_txt = 'TELEVISOR',
            codigo   = tv.codigo,
            linea1   = f'{tv.marca} {tv.modelo}{pulg}',
            linea2   = f'Aula: {aula}',
            linea3   = f'N° serie: {tv.numero_serie or "—"}',
            detalle  = comp,
            st=st, W=W,
        ))

    # ── Pantallas Digitales ───────────────────────────────────────────────────
    for item in pantallas_data:
        p, ubic = item['equipo'], item['ubic']
        nombre = getattr(p, 'nombre', f'Pantalla #{p.id}')
        marca  = getattr(p, 'marca', '')
        modelo = getattr(p, 'modelo', '')
        aula   = ubic.aula + (f' — {ubic.sector}' if ubic.sector else '')
        celdas.append(_armar_etiqueta(
            color    = _VERDE,
            tipo_txt = 'PANTALLA DIGITAL',
            codigo   = f'PD-{p.id:02d}',
            linea1   = nombre,
            linea2   = f'{marca} {modelo}'.strip() or '—',
            linea3   = f'Aula: {aula}',
            detalle  = '',
            st=st, W=W,
        ))

    # ── Impresoras 3D ─────────────────────────────────────────────────────────
    for item in impresoras_data:
        imp, ubic = item['equipo'], item['ubic']
        num    = getattr(imp, 'numero_interno', imp.id)
        marca  = getattr(imp, 'marca', '')
        modelo = getattr(imp, 'modelo', '')
        serie  = getattr(imp, 'numero_serie', None)
        aula   = ubic.aula + (f' — {ubic.sector}' if ubic.sector else '')
        celdas.append(_armar_etiqueta(
            color    = _NARANJA,
            tipo_txt = 'IMPRESORA 3D',
            codigo   = f'IMP-{num:02d}',
            linea1   = f'{marca} {modelo}'.strip() or '—',
            linea2   = f'Aula: {aula}',
            linea3   = f'N° serie: {serie or "—"}',
            detalle  = '',
            st=st, W=W,
        ))

    if celdas:
        story.append(_grid_etiquetas(celdas, W, H, COLS))
    else:
        story.append(Paragraph('No hay equipos con ubicación registrada.', _st()['sub']))

    doc.build(story)
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# Helpers internos
# ─────────────────────────────────────────────────────────────────────────────

def _armar_etiqueta(color, tipo_txt, codigo, linea1, linea2, linea3, detalle, st, W):
    """Construye el contenido de una etiqueta individual como lista de flowables."""
    celda = [
        Table(
            [[Paragraph(f'<b>{tipo_txt}</b>  ·  {codigo}', st['et'])]],
            colWidths=[W - 6],
            style=[('BACKGROUND',    (0,0),(-1,-1), color),
                   ('TOPPADDING',    (0,0),(-1,-1), 4),
                   ('BOTTOMPADDING', (0,0),(-1,-1), 4)],
        ),
        Spacer(1, 1.5*mm),
    ]
    if linea1:  celda.append(Paragraph(f'<b>{linea1}</b>', st['em']))
    if linea2:  celda.append(Paragraph(linea2,              st['em']))
    if linea3:  celda.append(Paragraph(linea3,              st['es']))
    if detalle:
        celda.append(HRFlowable(width=W - 12, thickness=0.5, color=colors.lightgrey))
        celda.append(Paragraph(f'<i>{detalle}</i>', st['es']))
    return celda


def _grid_etiquetas(celdas, W, H, COLS):
    """Organiza las celdas en una tabla de N columnas."""
    filas = []
    fila  = []
    for celda in celdas:
        fila.append(celda)
        if len(fila) == COLS:
            filas.append(fila)
            fila = []
    if fila:
        while len(fila) < COLS:
            fila.append('')
        filas.append(fila)

    t = Table(filas,
              colWidths=[W] * COLS,
              rowHeights=[H] * len(filas))
    t.setStyle(TableStyle([
        ('BOX',         (0,0), (-1,-1), 0.8, colors.grey),
        ('INNERGRID',   (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('VALIGN',      (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING',  (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 3),
        ('RIGHTPADDING',(0,0), (-1,-1), 3),
    ]))
    return t
