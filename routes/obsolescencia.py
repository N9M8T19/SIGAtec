"""
routes/obsolescencia.py
Módulo de Obsolescencia y Reemplazos de Netbooks.
Accesible para todos los roles (Encargado, Directivo, Administrador).
"""

from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, Netbook, Carro, Usuario
import os
import psycopg2
import psycopg2.extras

ARG_OFFSET = timedelta(hours=-3)

obsolescencia_bp = Blueprint("obsolescencia", __name__, url_prefix="/obsolescencia")


def _get_conn():
    return psycopg2.connect(os.environ["DATABASE_URL"])


def _fetch_all(sql, params=None):
    conn = _get_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(sql, params or ())
        rows = cur.fetchall()
        cur.close()
        return rows
    finally:
        conn.close()


def _fetch_one(sql, params=None):
    conn = _get_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(sql, params or ())
        row = cur.fetchone()
        cur.close()
        return row
    finally:
        conn.close()


def _execute(sql, params=None):
    conn = _get_conn()
    conn.autocommit = True
    try:
        cur = conn.cursor()
        cur.execute(sql, params or ())
        cur.close()
    finally:
        conn.close()


# ─────────────────────────────────────────────
# INDEX
# ─────────────────────────────────────────────

@obsolescencia_bp.route("/")
@login_required
def index():
    filtro = request.args.get("filtro", "todas")

    sql_base = """
        SELECT o.id, o.motivo, o.observaciones, o.fecha_baja,
               o.tiene_reemplazo, o.reemplazo_serie, o.reemplazo_modelo,
               o.reemplazo_pendiente, o.fecha_reemplazo,
               o.reemplazo_carro_id,
               n.numero_serie, n.numero_interno,
               c.numero_fisico AS carro_numero,
               u1.username AS registrado_por,
               u2.username AS reemplazo_registrado_por,
               c2.numero_fisico AS carro_reemplazo_numero
        FROM obsolescencias o
        JOIN netbooks n ON n.id = o.netbook_id
        LEFT JOIN carros c ON c.id = n.carro_id
        LEFT JOIN usuarios u1 ON u1.id = o.registrado_por
        LEFT JOIN usuarios u2 ON u2.id = o.reemplazo_registrado_por
        LEFT JOIN carros c2 ON c2.id = o.reemplazo_carro_id
    """

    where = ""
    if filtro == "pendientes":
        where = " WHERE o.reemplazo_pendiente = TRUE"
    elif filtro == "con_reemplazo":
        where = " WHERE o.tiene_reemplazo = TRUE AND o.reemplazo_pendiente = FALSE"
    elif filtro == "sin_reemplazo":
        where = " WHERE o.tiene_reemplazo = FALSE"

    rows = _fetch_all(sql_base + where + " ORDER BY o.fecha_baja DESC")

    carros = Carro.query.filter_by(estado="activo").order_by(Carro.numero_fisico).all()

    pendiente = _fetch_one("SELECT COUNT(*) AS total FROM obsolescencias WHERE reemplazo_pendiente = TRUE")
    total_pendientes = pendiente["total"] if pendiente else 0

    return render_template(
        "obsolescencia/index.html",
        rows=rows,
        filtro=filtro,
        carros=carros,
        total_pendientes=total_pendientes,
    )


# ─────────────────────────────────────────────
# NUEVA OBSOLESCENCIA
# ─────────────────────────────────────────────

@obsolescencia_bp.route("/nueva", methods=["GET", "POST"])
@login_required
def nueva():
    carros = Carro.query.order_by(Carro.numero_fisico).all()

    if request.method == "POST":
        netbook_id = request.form.get("netbook_id")
        motivo = request.form.get("motivo", "").strip()
        observaciones = request.form.get("observaciones", "").strip()

        if not netbook_id or not motivo:
            flash("Completá todos los campos obligatorios.", "danger")
            return render_template("obsolescencia/nueva.html", carros=carros)

        netbook = Netbook.query.get(netbook_id)
        if not netbook:
            flash("Netbook no encontrada.", "danger")
            return redirect(url_for("obsolescencia.index"))

        netbook.estado = "de_baja"
        db.session.commit()

        _execute("""
            INSERT INTO obsolescencias
                (netbook_id, motivo, observaciones, fecha_baja, registrado_por,
                 tiene_reemplazo, reemplazo_pendiente)
            VALUES (%s, %s, %s, %s, %s, FALSE, FALSE)
        """, (
            int(netbook_id),
            motivo,
            observaciones or None,
            datetime.utcnow(),
            current_user.id,
        ))

        flash(f"Netbook N°{netbook.numero_interno} — serie {netbook.numero_serie} registrada como obsoleta.", "success")
        return redirect(url_for("obsolescencia.index"))

    carro_id = request.args.get("carro_id")
    netbooks_carro = []
    if carro_id:
        netbooks_carro = Netbook.query.filter_by(
            carro_id=int(carro_id), estado="activo"
        ).order_by(Netbook.numero_interno).all()

    return render_template(
        "obsolescencia/nueva.html",
        carros=carros,
        carro_id_sel=carro_id,
        netbooks_carro=netbooks_carro,
    )


# ─────────────────────────────────────────────
# AJAX — netbooks de un carro
# ─────────────────────────────────────────────

@obsolescencia_bp.route("/netbooks-de-carro/<int:carro_id>")
@login_required
def netbooks_de_carro(carro_id):
    netbooks = Netbook.query.filter(
        Netbook.carro_id == carro_id,
        Netbook.estado.in_(["activo", "en_servicio"])
    ).order_by(Netbook.numero_interno).all()
    data = [
        {
            "id": n.id,
            "numero_interno": n.numero_interno,
            "numero_serie": n.numero_serie,
            "estado": n.estado,
        }
        for n in netbooks
    ]
    return jsonify(data)


# ─────────────────────────────────────────────
# REGISTRAR REEMPLAZO
# ─────────────────────────────────────────────

@obsolescencia_bp.route("/<int:obs_id>/reemplazo", methods=["GET", "POST"])
@login_required
def registrar_reemplazo(obs_id):
    obs = _fetch_one("""
        SELECT o.*, n.numero_serie AS nb_serie, n.numero_interno AS nb_interno,
               c.numero_fisico AS carro_numero, n.carro_id AS nb_carro_id
        FROM obsolescencias o
        JOIN netbooks n ON n.id = o.netbook_id
        LEFT JOIN carros c ON c.id = n.carro_id
        WHERE o.id = %s
    """, (obs_id,))

    if not obs:
        flash("Registro no encontrado.", "danger")
        return redirect(url_for("obsolescencia.index"))

    carros = Carro.query.filter_by(estado="activo").order_by(Carro.numero_fisico).all()

    if request.method == "POST":
        reemplazo_serie = request.form.get("reemplazo_serie", "").strip()
        reemplazo_modelo = request.form.get("reemplazo_modelo", "").strip()
        destino = request.form.get("destino")
        carro_destino_id = request.form.get("carro_destino_id")
        numero_interno_nuevo = request.form.get("numero_interno_nuevo", "").strip()

        if not reemplazo_serie:
            flash("Ingresá el número de serie de la netbook nueva.", "danger")
            return render_template("obsolescencia/reemplazo.html", obs=obs, carros=carros)

        fecha_reemplazo = datetime.utcnow()

        if destino == "carro" and carro_destino_id:
            carro_obj = Carro.query.get(int(carro_destino_id))
            if not carro_obj:
                flash("Carro no encontrado.", "danger")
                return render_template("obsolescencia/reemplazo.html", obs=obs, carros=carros)

            existente_serie = Netbook.query.filter_by(numero_serie=reemplazo_serie).first()
            if existente_serie:
                flash(f"El número de serie {reemplazo_serie} ya está registrado en el sistema.", "danger")
                return render_template("obsolescencia/reemplazo.html", obs=obs, carros=carros)

            nueva_nb = Netbook(
                carro_id=int(carro_destino_id),
                numero_serie=reemplazo_serie,
                numero_interno=numero_interno_nuevo or obs["nb_interno"],
                estado="activo",
            )
            db.session.add(nueva_nb)
            db.session.commit()

            _execute("""
                UPDATE obsolescencias SET
                    tiene_reemplazo = TRUE,
                    reemplazo_pendiente = FALSE,
                    reemplazo_serie = %s,
                    reemplazo_modelo = %s,
                    reemplazo_carro_id = %s,
                    fecha_reemplazo = %s,
                    reemplazo_registrado_por = %s
                WHERE id = %s
            """, (reemplazo_serie, reemplazo_modelo or None,
                  int(carro_destino_id), fecha_reemplazo, current_user.id, obs_id))

            flash(f"Netbook nueva ({reemplazo_serie}) registrada y asignada al Carro {carro_obj.numero_fisico}.", "success")

        else:
            _execute("""
                UPDATE obsolescencias SET
                    tiene_reemplazo = TRUE,
                    reemplazo_pendiente = TRUE,
                    reemplazo_serie = %s,
                    reemplazo_modelo = %s,
                    fecha_reemplazo = %s,
                    reemplazo_registrado_por = %s
                WHERE id = %s
            """, (reemplazo_serie, reemplazo_modelo or None,
                  fecha_reemplazo, current_user.id, obs_id))

            flash("Reemplazo registrado como PENDIENTE DE ASIGNACIÓN. Aparecerá en Novedades del día.", "warning")

        return redirect(url_for("obsolescencia.index"))

    return render_template("obsolescencia/reemplazo.html", obs=obs, carros=carros)


# ─────────────────────────────────────────────
# ASIGNAR CARRO A REEMPLAZO PENDIENTE
# ─────────────────────────────────────────────

@obsolescencia_bp.route("/<int:obs_id>/asignar-carro", methods=["POST"])
@login_required
def asignar_carro(obs_id):
    obs = _fetch_one("SELECT * FROM obsolescencias WHERE id = %s", (obs_id,))
    if not obs or not obs["reemplazo_pendiente"]:
        flash("Registro no encontrado o ya asignado.", "danger")
        return redirect(url_for("obsolescencia.index"))

    carro_destino_id = request.form.get("carro_destino_id")
    numero_interno_nuevo = request.form.get("numero_interno_nuevo", "").strip()

    if not carro_destino_id:
        flash("Seleccioná un carro destino.", "danger")
        return redirect(url_for("obsolescencia.index"))

    carro_obj = Carro.query.get(int(carro_destino_id))
    if not carro_obj:
        flash("Carro no encontrado.", "danger")
        return redirect(url_for("obsolescencia.index"))

    reemplazo_serie = obs["reemplazo_serie"]
    existente_serie = Netbook.query.filter_by(numero_serie=reemplazo_serie).first()
    if existente_serie:
        flash(f"El número de serie {reemplazo_serie} ya fue ingresado al sistema.", "danger")
        return redirect(url_for("obsolescencia.index"))

    netbook_orig = _fetch_one("SELECT * FROM netbooks WHERE id = %s", (obs["netbook_id"],))

    nueva_nb = Netbook(
        carro_id=int(carro_destino_id),
        numero_serie=reemplazo_serie,
        numero_interno=numero_interno_nuevo or (netbook_orig["numero_interno"] if netbook_orig else ""),
        estado="activo",
    )
    db.session.add(nueva_nb)
    db.session.commit()

    _execute("""
        UPDATE obsolescencias SET
            reemplazo_pendiente = FALSE,
            reemplazo_carro_id = %s
        WHERE id = %s
    """, (int(carro_destino_id), obs_id))

    flash(f"Netbook {reemplazo_serie} asignada al Carro {carro_obj.numero_fisico}. ✅", "success")
    return redirect(url_for("obsolescencia.index"))


# ─────────────────────────────────────────────
# API — pendientes para Novedades del día
# ─────────────────────────────────────────────

@obsolescencia_bp.route("/api/pendientes")
@login_required
def api_pendientes():
    rows = _fetch_all("""
        SELECT o.id, o.reemplazo_serie, o.reemplazo_modelo, o.fecha_reemplazo,
               n.numero_serie AS nb_serie, n.numero_interno AS nb_interno
        FROM obsolescencias o
        JOIN netbooks n ON n.id = o.netbook_id
        WHERE o.reemplazo_pendiente = TRUE
        ORDER BY o.fecha_reemplazo DESC
    """)
    return jsonify([dict(r) for r in rows])
