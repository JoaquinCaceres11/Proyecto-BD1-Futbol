from datetime import datetime
from flask import flash, redirect, request, session, url_for
from db import consulta, ejecutar
from helpers import accion, admin, ambos, campo, formulario, form_get, opciones, pagina, tabla, validar


def datos_partido(id_partido):
    r = consulta(
        "SELECT p.*, el.nombre AS local, ev.nombre AS visitante, "
        "(p.estado = 'jugado' AND TIMESTAMPDIFF(HOUR, p.fecha_jugado, NOW()) >= 48) AS corregible_vencido "
        "FROM partido p JOIN equipo el ON el.id_equipo = p.id_equipo_local "
        "JOIN equipo ev ON ev.id_equipo = p.id_equipo_visitante WHERE p.id_partido = %s",
        (id_partido,),
    )
    return r[0] if r else None


def planilla_editable(p):
    if p["estado"] not in ("programado", "jugado"):
        return False, "Solo se puede cargar planilla en partidos programados o jugados."
    if p["corregible_vencido"]:
        return False, "Pasaron mas de 48 horas desde que se jugo el partido: el resultado ya no puede corregirse."
    return True, ""


def _planilla_accion(id_partido, fn):
    p = datos_partido(id_partido)
    if not p:
        flash("El partido no existe.", "error")
        return redirect(url_for("partidos"))
    ok, motivo = planilla_editable(p)
    if not ok:
        flash(motivo, "error")
    else:
        fn(p)
    return redirect(url_for("planilla", id_partido=id_partido))


def _minuto_valido(txt):
    if txt.isdigit() and 1 <= int(txt) <= 60:
        return True
    flash("El minuto debe estar entre 1 y 60.", "error")
    return False


def register_partidos_routes(app):
    @app.route("/partidos", methods=["GET", "POST"])
    @ambos
    def partidos():
        if request.method == "POST":
            if session["rol"] != "administrador":
                flash("Solo el administrador puede programar partidos.", "error")
                return redirect(url_for("partidos"))

            keys = ["id_torneo", "numero_fecha", "id_equipo_local", "id_equipo_visitante", "dia", "id_turno", "cancha"]
            f = dict(zip(keys, form_get(*keys)))

            dia = None
            try:
                dia = datetime.strptime(f["dia"], "%Y-%m-%d").date()
            except ValueError:
                pass

            t = consulta("SELECT estado, fecha_inicio, fecha_fin FROM torneo WHERE id_torneo = %s", (f["id_torneo"],)) if f["id_torneo"].isdigit() else []
            campos_ok = all(f[k].isdigit() for k in ["id_torneo", "numero_fecha", "id_equipo_local", "id_equipo_visitante", "id_turno"]) and "|" in f["cancha"]

            if validar([
                (campos_ok, "Completa todos los campos del partido."),
                (f["id_equipo_local"] != f["id_equipo_visitante"], "Un equipo no puede enfrentarse a si mismo."),
                (dia is not None, "La fecha del partido no es valida."),
                (t and t[0]["estado"] == "en curso", "El torneo debe estar 'en curso' para programar partidos."),
                (dia and t and t[0]["fecha_inicio"] <= dia <= t[0]["fecha_fin"], "El dia del partido esta fuera de las fechas del torneo."),
            ]):
                cancha, comp_id = f["cancha"].split("|")
                ejecutar(
                    "INSERT INTO partido (id_torneo, numero_fecha, id_equipo_local, id_equipo_visitante, dia, id_turno, nombre_cancha, id_complejo) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                    (int(f["id_torneo"]), int(f["numero_fecha"]), int(f["id_equipo_local"]), int(f["id_equipo_visitante"]),
                     f["dia"], int(f["id_turno"]), cancha, int(comp_id)),
                    "Partido programado.",
                )
            return redirect(url_for("partidos"))

        filas = consulta(
            "SELECT p.id_partido AS id, p.numero_fecha AS fecha, p.dia, CONCAT(t.hora_inicio, '-', t.hora_fin) AS turno, "
            "el.nombre AS local, ev.nombre AS visitante, CONCAT(p.nombre_cancha, ' / ', c.nombre) AS cancha, "
            "p.estado, CONCAT(r.goles_local, ' - ', r.goles_visitante) AS resultado "
            "FROM partido p JOIN equipo el ON el.id_equipo = p.id_equipo_local JOIN equipo ev ON ev.id_equipo = p.id_equipo_visitante "
            "JOIN turno t ON t.id_turno = p.id_turno JOIN complejo c ON c.id_complejo = p.id_complejo "
            "LEFT JOIN v_resultado_partido r ON r.id_partido = p.id_partido ORDER BY p.numero_fecha, p.dia, t.hora_inicio"
        )
        es_admin = session["rol"] == "administrador"
        for r in filas:
            a = [accion("Planilla", url_for("planilla", id_partido=r["id"]), "get")]
            if r["estado"] in ("programado", "postergado"):
                a.append(accion("Marcar jugado", url_for("partido_estado", id_partido=r["id"]), datos={"estado": "jugado"}, confirmar=True))
            if es_admin:
                if r["estado"] == "programado":
                    a.append(accion("Postergar", url_for("partido_estado", id_partido=r["id"]), datos={"estado": "postergado"}, confirmar=True))
                if r["estado"] in ("programado", "postergado"):
                    a.append(accion("Cancelar", url_for("partido_estado", id_partido=r["id"]), datos={"estado": "cancelado"}, confirmar=True))
                a.append(accion("Eliminar", url_for("partido_eliminar", id_partido=r["id"]), confirmar=True))
            r["_acciones"] = a

        formularios = []
        if es_admin:
            eqs = opciones("SELECT id_equipo AS valor, CONCAT(nombre, ' (torneo ', id_torneo, ')') AS texto FROM equipo ORDER BY id_torneo, nombre")
            canchas_op = opciones(
                "SELECT CONCAT(c.nombre_cancha, '|', c.id_complejo) AS valor, CONCAT(c.nombre_cancha, ' - ', x.nombre) AS texto "
                "FROM cancha c JOIN complejo x ON x.id_complejo = c.id_complejo ORDER BY x.nombre, c.nombre_cancha"
            )
            formularios.append(formulario("Programar partido", url_for("partidos"), [
                campo("id_torneo", "Torneo", "select", opciones("SELECT id_torneo AS valor, nombre AS texto FROM torneo WHERE estado = 'en curso'")),
                campo("numero_fecha", "Numero de fecha", "number", extra='required min="1"'),
                campo("id_equipo_local", "Local", "select", eqs),
                campo("id_equipo_visitante", "Visitante", "select", eqs),
                campo("dia", "Dia", "date", extra="required"),
                campo("id_turno", "Turno", "select", opciones("SELECT id_turno AS valor, CONCAT(hora_inicio, ' a ', hora_fin) AS texto FROM turno")),
                campo("cancha", "Cancha", "select", canchas_op),
            ], "Programar"))

        return pagina("Partidos", formularios,
                      [tabla("Fixture", ["id", "fecha", "dia", "turno", "local", "visitante", "cancha", "estado", "resultado"], filas, True)])

    @app.route("/partidos/<int:id_partido>/estado", methods=["POST"])
    @ambos
    def partido_estado(id_partido):
        nuevo = request.form.get("estado")
        if nuevo not in ("jugado", "postergado", "cancelado"):
            flash("Estado invalido.", "error")
        elif nuevo != "jugado" and session["rol"] != "administrador":
            flash("Solo el administrador puede postergar o cancelar partidos.", "error")
        else:
            ejecutar(
                "UPDATE partido SET estado = %s WHERE id_partido = %s AND estado IN ('programado','postergado')",
                (nuevo, id_partido),
                f"Partido marcado como {nuevo}.",
            )
        return redirect(url_for("partidos"))

    @app.route("/partidos/<int:id_partido>/eliminar", methods=["POST"])
    @admin
    def partido_eliminar(id_partido):
        ejecutar("DELETE FROM partido WHERE id_partido = %s", (id_partido,), "Partido eliminado.")
        return redirect(url_for("partidos"))

    @app.route("/partidos/<int:id_partido>/planilla")
    @ambos
    def planilla(id_partido):
        p = datos_partido(id_partido)
        if not p:
            flash("El partido no existe.", "error")
            return redirect(url_for("partidos"))
        editable, motivo = planilla_editable(p)

        res = consulta("SELECT goles_local, goles_visitante FROM v_resultado_partido WHERE id_partido = %s", (id_partido,))
        resultado = f"{res[0]['goles_local']} - {res[0]['goles_visitante']}" if res else "(se calcula al marcar jugado)"

        jug = consulta(
            "SELECT pp.ci_jugador AS ci, CONCAT(j.apellido, ', ', j.nombre) AS jugador, e.nombre AS equipo "
            "FROM planilla_partido pp JOIN jugador j ON j.ci = pp.ci_jugador "
            "JOIN equipo e ON e.id_equipo = pp.id_equipo WHERE pp.id_partido = %s ORDER BY e.nombre",
            (id_partido,),
        )
        goles = consulta(
            "SELECT g.id_gol AS id, CONCAT(j.apellido, ', ', j.nombre) AS jugador, g.minuto, "
            "IF(g.autogol, 'Si', 'No') AS autogol FROM gol g JOIN jugador j ON j.ci = g.ci_jugador "
            "WHERE g.id_partido = %s ORDER BY g.minuto",
            (id_partido,),
        )
        tarj = consulta(
            "SELECT t.id_tarjeta AS id, CONCAT(j.apellido, ', ', j.nombre) AS jugador, t.minuto, t.color "
            "FROM tarjeta t JOIN jugador j ON j.ci = t.ci_jugador WHERE t.id_partido = %s ORDER BY t.minuto",
            (id_partido,),
        )

        for r in jug:
            r["_acciones"] = [accion("Quitar", url_for("planilla_quitar", id_partido=id_partido), datos={"ci_jugador": r["ci"]}, confirmar=True)]
        for r in goles:
            r["_acciones"] = [accion("Eliminar", url_for("gol_eliminar", id_partido=id_partido), datos={"id": r["id"]}, confirmar=True)]
        for r in tarj:
            r["_acciones"] = [accion("Eliminar", url_for("tarjeta_eliminar", id_partido=id_partido), datos={"id": r["id"]}, confirmar=True)]

        formularios = []
        if editable:
            candidatos = opciones(
                "SELECT j.ci AS valor, CONCAT(j.apellido, ', ', j.nombre, ' - ', e.nombre) AS texto "
                "FROM equipo_jugador_torneo ejt JOIN jugador j ON j.ci = ejt.ci_jugador "
                "JOIN equipo e ON e.id_equipo = ejt.id_equipo WHERE ejt.id_equipo IN (%s, %s) AND ejt.ci_jugador NOT IN "
                "(SELECT ci_jugador FROM planilla_partido WHERE id_partido = %s) ORDER BY e.nombre, j.apellido",
                (p["id_equipo_local"], p["id_equipo_visitante"], id_partido),
            )
            en_planilla = [(r["ci"], r["jugador"] + " - " + r["equipo"]) for r in jug]
            formularios = [
                formulario("Agregar jugador a la planilla", url_for("planilla_agregar", id_partido=id_partido),
                           [campo("ci_jugador", "Jugador (plantel de alguno de los dos equipos)", "select", candidatos)], "Agregar"),
                formulario("Registrar gol", url_for("gol_agregar", id_partido=id_partido), [
                    campo("ci_jugador", "Jugador", "select", en_planilla),
                    campo("minuto", "Minuto", "number", extra='required min="1" max="60"'),
                    campo("autogol", "Autogol", "checkbox"),
                ], "Registrar gol"),
                formulario("Registrar tarjeta", url_for("tarjeta_agregar", id_partido=id_partido), [
                    campo("ci_jugador", "Jugador", "select", en_planilla),
                    campo("minuto", "Minuto", "number", extra='required min="1" max="60"'),
                    campo("color", "Color", "select", [("amarilla", "amarilla"), ("roja", "roja")]),
                ], "Registrar tarjeta"),
            ]
        elif motivo:
            flash(motivo, "error")

        sub = f"Fecha {p['numero_fecha']} - {p['dia']} - Estado: {p['estado']} - {p['local']} vs {p['visitante']} - Resultado: {resultado}"
        return pagina("Planilla de juego", formularios,
                      [tabla("Jugadores en la planilla", ["ci", "jugador", "equipo"], jug, editable),
                       tabla("Goles", ["jugador", "minuto", "autogol"], goles, editable),
                       tabla("Tarjetas", ["jugador", "minuto", "color"], tarj, editable)], subtitulo=sub)

    @app.route("/partidos/<int:id_partido>/planilla/agregar", methods=["POST"])
    @ambos
    def planilla_agregar(id_partido):
        ci = request.form.get("ci_jugador", "")
        def hacer(p):
            eq = consulta("SELECT id_equipo FROM equipo_jugador_torneo WHERE ci_jugador = %s AND id_equipo IN (%s,%s)",
                          (ci, p["id_equipo_local"], p["id_equipo_visitante"]))
            if not eq:
                flash("El jugador no integra el plantel de ninguno de los dos equipos.", "error")
            else:
                ejecutar("INSERT INTO planilla_partido (id_partido, ci_jugador, id_equipo) VALUES (%s,%s,%s)",
                         (id_partido, ci, eq[0]["id_equipo"]), "Jugador agregado a la planilla.")
        return _planilla_accion(id_partido, hacer)

    @app.route("/partidos/<int:id_partido>/planilla/quitar", methods=["POST"])
    @ambos
    def planilla_quitar(id_partido):
        return _planilla_accion(id_partido, lambda p: ejecutar(
            "DELETE FROM planilla_partido WHERE id_partido = %s AND ci_jugador = %s",
            (id_partido, request.form.get("ci_jugador", "")), "Jugador quitado de la planilla."))

    @app.route("/partidos/<int:id_partido>/gol", methods=["POST"])
    @ambos
    def gol_agregar(id_partido):
        ci, min_ = form_get("ci_jugador", "minuto")
        if not _minuto_valido(min_):
            return redirect(url_for("planilla", id_partido=id_partido))
        return _planilla_accion(id_partido, lambda p: ejecutar(
            "INSERT INTO gol (id_partido, ci_jugador, minuto, autogol) VALUES (%s,%s,%s,%s)",
            (id_partido, ci, int(min_), 1 if request.form.get("autogol") else 0), "Gol registrado."))

    @app.route("/partidos/<int:id_partido>/gol/eliminar", methods=["POST"])
    @ambos
    def gol_eliminar(id_partido):
        return _planilla_accion(id_partido, lambda p: ejecutar(
            "DELETE FROM gol WHERE id_gol = %s AND id_partido = %s", (request.form.get("id"), id_partido), "Gol eliminado."))

    @app.route("/partidos/<int:id_partido>/tarjeta", methods=["POST"])
    @ambos
    def tarjeta_agregar(id_partido):
        ci, min_, col = form_get("ci_jugador", "minuto", "color")
        if col not in ("amarilla", "roja"):
            flash("Color de tarjeta invalido.", "error")
            return redirect(url_for("planilla", id_partido=id_partido))
        if not _minuto_valido(min_):
            return redirect(url_for("planilla", id_partido=id_partido))
        return _planilla_accion(id_partido, lambda p: ejecutar(
            "INSERT INTO tarjeta (id_partido, ci_jugador, minuto, color) VALUES (%s,%s,%s,%s)",
            (id_partido, ci, int(min_), col), "Tarjeta registrada (la sancion automatica, si corresponde, se genera sola)."))

    @app.route("/partidos/<int:id_partido>/tarjeta/eliminar", methods=["POST"])
    @ambos
    def tarjeta_eliminar(id_partido):
        return _planilla_accion(id_partido, lambda p: ejecutar(
            "DELETE FROM tarjeta WHERE id_tarjeta = %s AND id_partido = %s", (request.form.get("id"), id_partido), "Tarjeta eliminada."))

