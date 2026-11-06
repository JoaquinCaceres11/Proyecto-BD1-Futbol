from datetime import datetime
from flask import flash, redirect, request, session, url_for
from db import consulta, ejecutar
from helpers import accion, admin, ambos, campo, cuenta, fila, formulario, form_get, opciones, pagina, tabla, validar


def datos_partido(id_partido):
    return fila(
        "SELECT p.*, el.nombre AS local, ev.nombre AS visitante, "
        "(TIMESTAMP(p.dia, t.hora_fin) > NOW()) AS no_disputado, "
        "(p.estado = 'jugado' AND NOW() > TIMESTAMP(p.dia, t.hora_fin) + INTERVAL 48 HOUR) AS vencido "
        "FROM partido p JOIN equipo el ON el.id_equipo = p.id_equipo_local "
        "JOIN equipo ev ON ev.id_equipo = p.id_equipo_visitante JOIN turno t ON t.id_turno = p.id_turno "
        "WHERE p.id_partido = %s", (id_partido,))


def planilla_editable(p):
    if p["estado"] not in ("programado", "jugado"):
        return False, "Solo se puede cargar planilla en partidos programados o jugados."
    if p["no_disputado"]:
        return False, "El partido todavia no se disputo."
    if p["vencido"]:
        return False, "Pasaron mas de 48 horas desde la disputa: el resultado ya no puede modificarse."
    return True, ""


def _planilla_accion(id_partido, fn):
    p = datos_partido(id_partido)
    if not p:
        flash("El partido no existe.", "error")
        return redirect(url_for("partidos"))
    ok, msj = planilla_editable(p)
    if not ok:
        flash(msj, "error")
    else:
        fn(p)
    return redirect(url_for("planilla", id_partido=id_partido))


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
            cancha, comp_id = f["cancha"].split("|") if "|" in f["cancha"] else ("", "0")
            dia_ok = None
            try:
                dia_ok = datetime.strptime(f["dia"], "%Y-%m-%d").date()
            except ValueError:
                pass

            t = fila("SELECT estado, fecha_inicio, fecha_fin FROM torneo WHERE id_torneo = %s", (f["id_torneo"],))
            id_t, loc, vis, n_f, tur = int(f["id_torneo"] or 0), int(f["id_equipo_local"] or 0), int(f["id_equipo_visitante"] or 0), int(f["numero_fecha"] or 0), int(f["id_turno"] or 0)

            if validar([
                (t and t["estado"] == "en curso", "El torneo debe estar 'en curso'."),
                (dia_ok and t and t["fecha_inicio"] <= dia_ok <= t["fecha_fin"], "El dia esta fuera de las fechas del torneo."),
                (loc and vis and loc != vis, "Los equipos deben ser distintos."),
                (cuenta("SELECT COUNT(*) FROM equipo WHERE id_equipo = %s AND id_torneo = %s", (loc, id_t)) and
                 cuenta("SELECT COUNT(*) FROM equipo WHERE id_equipo = %s AND id_torneo = %s", (vis, id_t)), "Ambos equipos deben pertenecer al torneo."),
                (cuenta("SELECT COUNT(*) FROM equipo_jugador_torneo WHERE id_equipo = %s", (loc,)) >= 5 and
                 cuenta("SELECT COUNT(*) FROM equipo_jugador_torneo WHERE id_equipo = %s", (vis,)) >= 5, "Ambos equipos deben tener al menos 5 jugadores."),
                (cuenta("SELECT COUNT(*) FROM partido WHERE id_torneo = %s AND estado <> 'cancelado' AND "
                        "((id_equipo_local = %s AND id_equipo_visitante = %s) OR (id_equipo_local = %s AND id_equipo_visitante = %s))",
                        (id_t, loc, vis, vis, loc)) == 0, "Estos equipos ya tienen un partido en esta edicion."),
                (cuenta("SELECT COUNT(*) FROM partido WHERE id_torneo = %s AND numero_fecha = %s AND estado <> 'cancelado' AND "
                        "(id_equipo_local IN (%s,%s) OR id_equipo_visitante IN (%s,%s))", (id_t, n_f, loc, vis, loc, vis)) == 0,
                 "Uno de los equipos ya tiene partido asignado en esa fecha."),
                (cuenta("SELECT COUNT(*) FROM partido WHERE dia = %s AND id_turno = %s AND nombre_cancha = %s AND id_complejo = %s AND estado <> 'cancelado'",
                        (f["dia"], tur, cancha, comp_id)) == 0, "La cancha ya esta ocupada en ese dia y turno."),
            ]):
                ejecutar("INSERT INTO partido (id_torneo, numero_fecha, id_equipo_local, id_equipo_visitante, dia, id_turno, nombre_cancha, id_complejo) "
                         "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)", (id_t, n_f, loc, vis, f["dia"], tur, cancha, comp_id), "Partido programado.")
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
            if r["estado"] == "programado":
                a.append(accion("Marcar jugado", url_for("partido_estado", id_partido=r["id"]), datos={"estado": "jugado"}, confirmar=True))
            if es_admin:
                if r["estado"] == "programado":
                    a.append(accion("Postergar", url_for("partido_estado", id_partido=r["id"]), datos={"estado": "postergado"}, confirmar=True))
                if r["estado"] in ("programado", "postergado"):
                    a.append(accion("Cancelar", url_for("partido_estado", id_partido=r["id"]), datos={"estado": "cancelado"}, confirmar=True))
                if r["estado"] in ("programado", "postergado"):
                    a.append(accion("Modificar", url_for("partido_reprogramar", id_partido=r["id"]), "get"))
                a.append(accion("Eliminar", url_for("partido_eliminar", id_partido=r["id"]), confirmar=True))
            r["_acciones"] = a

        formularios = []
        if es_admin:
            eqs = opciones("SELECT id_equipo AS valor, CONCAT(nombre, ' (torneo ', id_torneo, ')') AS texto FROM equipo ORDER BY id_torneo, nombre")
            canchas = opciones("SELECT CONCAT(c.nombre_cancha, '|', c.id_complejo) AS valor, CONCAT(c.nombre_cancha, ' - ', x.nombre) AS texto "
                               "FROM cancha c JOIN complejo x ON x.id_complejo = c.id_complejo ORDER BY x.nombre, c.nombre_cancha")
            formularios.append(formulario("Programar partido", url_for("partidos"), [
                campo("id_torneo", "Torneo", "select", opciones("SELECT id_torneo AS valor, nombre AS texto FROM torneo WHERE estado = 'en curso'")),
                campo("numero_fecha", "Numero de fecha", "number", extra='required min="1"'),
                campo("id_equipo_local", "Local", "select", eqs),
                campo("id_equipo_visitante", "Visitante", "select", eqs),
                campo("dia", "Dia", "date", extra="required"),
                campo("id_turno", "Turno", "select", opciones("SELECT id_turno AS valor, CONCAT(hora_inicio, ' a ', hora_fin) AS texto FROM turno")),
                campo("cancha", "Cancha", "select", canchas),
            ], "Programar"))

        return pagina("Partidos", formularios, [tabla("Fixture", ["id", "fecha", "dia", "turno", "local", "visitante", "cancha", "estado", "resultado"], filas, True)])

    @app.route("/partidos/<int:id_partido>/estado", methods=["POST"])
    @ambos
    def partido_estado(id_partido):
        nuevo = request.form.get("estado")
        p = datos_partido(id_partido)
        if not p or nuevo not in ("jugado", "postergado", "cancelado"):
            flash("Operacion no valida.", "error")
        elif p["estado"] in ("jugado", "cancelado"):
            flash("Un partido jugado o cancelado no puede cambiar de estado.", "error")
        elif nuevo != "jugado" and session["rol"] != "administrador":
            flash("Solo el administrador puede postergar o cancelar partidos.", "error")
        elif nuevo == "jugado":
            if p["estado"] == "postergado":
                flash("Un partido postergado debe reprogramarse antes de marcarse jugado.", "error")
            elif p["no_disputado"]:
                flash("El dia y turno del partido todavia no pasaron.", "error")
            elif cuenta("SELECT COUNT(*) FROM planilla_partido WHERE id_partido = %s AND id_equipo = %s", (id_partido, p["id_equipo_local"])) == 0 or \
                 cuenta("SELECT COUNT(*) FROM planilla_partido WHERE id_partido = %s AND id_equipo = %s", (id_partido, p["id_equipo_visitante"])) == 0:
                flash("Carga la planilla de ambos equipos antes de marcar el partido como jugado.", "error")
            else:
                ejecutar("UPDATE partido SET estado = 'jugado', fecha_jugado = NOW() WHERE id_partido = %s", (id_partido,), "Partido marcado como jugado.")
        else:
            ejecutar("UPDATE partido SET estado = %s WHERE id_partido = %s", (nuevo, id_partido), f"Partido marcado como {nuevo}.")
        return redirect(url_for("partidos"))

    @app.route("/partidos/<int:id_partido>/reprogramar", methods=["GET", "POST"])
    @admin
    def partido_reprogramar(id_partido):
        p = datos_partido(id_partido)
        if not p or p["estado"] not in ("programado", "postergado"):
            flash("Solo se pueden modificar partidos programados o postergados.", "error")
            return redirect(url_for("partidos"))
        if cuenta("SELECT COUNT(*) FROM planilla_partido WHERE id_partido = %s", (id_partido,)) > 0:
            flash("No se puede modificar un partido que ya tiene planilla cargada.", "error")
            return redirect(url_for("partidos"))

        if request.method == "POST":
            num_f, dia, tur, cancha_str = form_get("numero_fecha", "dia", "id_turno", "cancha")
            nom_cancha, comp_id = cancha_str.split("|") if "|" in cancha_str else ("", "0")
            n_f = int(num_f) if num_f.isdigit() else 0
            id_tur = int(tur) if tur.isdigit() else 0
            try:
                dia_ok = datetime.strptime(dia, "%Y-%m-%d").date()
            except ValueError:
                flash("La fecha no es valida.", "error")
                return redirect(url_for("partido_reprogramar", id_partido=id_partido))

            t = fila("SELECT fecha_inicio, fecha_fin FROM torneo WHERE id_torneo = %s", (p["id_torneo"],))
            if validar([
                (n_f >= 1, "Numero de fecha invalido."),
                (id_tur, "Selecciona turno."),
                (nom_cancha, "Selecciona cancha."),
                (t["fecha_inicio"] <= dia_ok <= t["fecha_fin"], "El dia esta fuera de las fechas del torneo."),
                (p["estado"] != "postergado" or dia_ok != p["dia"] or id_tur != p["id_turno"], "Un partido postergado debe pasar a otro dia o turno."),
                (cuenta("SELECT COUNT(*) FROM partido WHERE dia = %s AND id_turno = %s AND nombre_cancha = %s AND id_complejo = %s AND estado <> 'cancelado' AND id_partido <> %s",
                        (dia, id_tur, nom_cancha, comp_id, id_partido)) == 0, "Cancha ocupada en ese dia y turno."),
                (cuenta("SELECT COUNT(*) FROM partido WHERE id_torneo = %s AND numero_fecha = %s AND estado <> 'cancelado' AND id_partido <> %s AND (id_equipo_local IN (%s,%s) OR id_equipo_visitante IN (%s,%s))",
                        (p["id_torneo"], n_f, id_partido, p["id_equipo_local"], p["id_equipo_visitante"], p["id_equipo_local"], p["id_equipo_visitante"])) == 0,
                 "Uno de los equipos ya tiene otro partido en esa fecha."),
            ]):
                ejecutar("UPDATE partido SET numero_fecha=%s, dia=%s, id_turno=%s, nombre_cancha=%s, id_complejo=%s, estado='programado' WHERE id_partido=%s",
                         (n_f, dia, id_tur, nom_cancha, comp_id, id_partido), "Partido modificado.")
                return redirect(url_for("partidos"))
            return redirect(url_for("partido_reprogramar", id_partido=id_partido))

        canchas = opciones("SELECT CONCAT(c.nombre_cancha, '|', c.id_complejo) AS valor, CONCAT(c.nombre_cancha, ' - ', x.nombre) AS texto FROM cancha c JOIN complejo x ON x.id_complejo = c.id_complejo ORDER BY x.nombre")
        form = formulario("Modificar partido", url_for("partido_reprogramar", id_partido=id_partido), [
            campo("numero_fecha", "Numero de fecha", "number", extra='required min="1"', valor=str(p["numero_fecha"])),
            campo("dia", "Dia", "date", extra="required", valor=str(p["dia"])),
            campo("id_turno", "Turno", "select", opciones("SELECT id_turno AS valor, CONCAT(hora_inicio, ' a ', hora_fin) AS texto FROM turno"), p["id_turno"]),
            campo("cancha", "Cancha", "select", canchas, f"{p['nombre_cancha']}|{p['id_complejo']}"),
        ], "Guardar cambios")
        return pagina("Modificar partido", [form], subtitulo=f"{p['local']} vs {p['visitante']} (Fecha {p['numero_fecha']} - {p['estado']})")

    @app.route("/partidos/<int:id_partido>/eliminar", methods=["POST"])
    @admin
    def partido_eliminar(id_partido):
        p = fila("SELECT estado FROM partido WHERE id_partido = %s", (id_partido,))
        if p and p["estado"] == "jugado":
            flash("Un partido jugado no puede eliminarse.", "error")
        else:
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
        res = fila("SELECT goles_local, goles_visitante FROM v_resultado_partido WHERE id_partido = %s", (id_partido,))
        resultado = f"{res['goles_local']} - {res['goles_visitante']}" if res else "(se calcula al marcar jugado)"

        jug = consulta("SELECT pp.ci_jugador AS ci, CONCAT(j.apellido, ', ', j.nombre) AS jugador, e.nombre AS equipo FROM planilla_partido pp "
                       "JOIN jugador j ON j.ci = pp.ci_jugador JOIN equipo e ON e.id_equipo = pp.id_equipo WHERE pp.id_partido = %s ORDER BY e.nombre", (id_partido,))
        goles = consulta("SELECT g.id_gol AS id, CONCAT(j.apellido, ', ', j.nombre) AS jugador, g.minuto, IF(g.autogol, 'Si', 'No') AS autogol "
                         "FROM gol g JOIN jugador j ON j.ci = g.ci_jugador WHERE g.id_partido = %s ORDER BY g.minuto", (id_partido,))
        tarj = consulta("SELECT t.id_tarjeta AS id, CONCAT(j.apellido, ', ', j.nombre) AS jugador, t.minuto, t.color "
                        "FROM tarjeta t JOIN jugador j ON j.ci = t.ci_jugador WHERE t.id_partido = %s ORDER BY t.minuto", (id_partido,))

        for r in jug: r["_acciones"] = [accion("Quitar", url_for("planilla_quitar", id_partido=id_partido), datos={"ci_jugador": r["ci"]}, confirmar=True)]
        for r in goles: r["_acciones"] = [accion("Eliminar", url_for("gol_eliminar", id_partido=id_partido), datos={"id": r["id"]}, confirmar=True)]
        for r in tarj: r["_acciones"] = [accion("Eliminar", url_for("tarjeta_eliminar", id_partido=id_partido), datos={"id": r["id"]}, confirmar=True)]

        formularios = []
        if editable:
            candidatos = opciones("SELECT j.ci AS valor, CONCAT(j.apellido, ', ', j.nombre, ' - ', e.nombre) AS texto "
                                  "FROM equipo_jugador_torneo ejt JOIN jugador j ON j.ci = ejt.ci_jugador JOIN equipo e ON e.id_equipo = ejt.id_equipo "
                                  "WHERE ejt.id_equipo IN (%s, %s) AND ejt.ci_jugador NOT IN (SELECT ci_jugador FROM planilla_partido WHERE id_partido = %s) ORDER BY e.nombre, j.apellido",
                                  (p["id_equipo_local"], p["id_equipo_visitante"], id_partido))
            en_plan = [(r["ci"], r["jugador"] + " - " + r["equipo"]) for r in jug]
            formularios = [
                formulario("Agregar jugador a la planilla", url_for("planilla_agregar", id_partido=id_partido), [campo("ci_jugador", "Jugador", "select", candidatos)], "Agregar"),
                formulario("Registrar gol", url_for("gol_agregar", id_partido=id_partido), [campo("ci_jugador", "Jugador", "select", en_plan), campo("minuto", "Minuto", "number", extra='required min="1" max="60"'), campo("autogol", "Autogol", "checkbox")], "Registrar gol"),
                formulario("Registrar tarjeta", url_for("tarjeta_agregar", id_partido=id_partido), [campo("ci_jugador", "Jugador", "select", en_plan), campo("minuto", "Minuto", "number", extra='required min="1" max="60"'), campo("color", "Color", "select", [("amarilla", "amarilla"), ("roja", "roja")])], "Registrar tarjeta"),
            ]
        elif motivo:
            flash(motivo, "error")

        sub = f"Fecha {p['numero_fecha']} - {p['dia']} - Estado: {p['estado']} - {p['local']} vs {p['visitante']} - Resultado: {resultado}"
        return pagina("Planilla de juego", formularios, [tabla("Jugadores", ["ci", "jugador", "equipo"], jug, editable),
                                                         tabla("Goles", ["jugador", "minuto", "autogol"], goles, editable),
                                                         tabla("Tarjetas", ["jugador", "minuto", "color"], tarj, editable)], subtitulo=sub)

    @app.route("/partidos/<int:id_partido>/planilla/agregar", methods=["POST"])
    @ambos
    def planilla_agregar(id_partido):
        ci = request.form.get("ci_jugador", "")
        def hacer(p):
            eq = fila("SELECT id_equipo FROM equipo_jugador_torneo WHERE ci_jugador = %s AND id_equipo IN (%s,%s)", (ci, p["id_equipo_local"], p["id_equipo_visitante"]))
            if not eq:
                flash("El jugador no integra el plantel de ninguno de los dos equipos.", "error")
            elif cuenta("SELECT COUNT(*) FROM sancion_jugador WHERE ci_jugador = %s AND id_torneo = %s AND %s >= numero_fecha_inicio AND %s < numero_fecha_inicio + cantidad_fechas",
                        (ci, p["id_torneo"], p["numero_fecha"], p["numero_fecha"])) > 0:
                flash("El jugador esta suspendido para esta fecha.", "error")
            else:
                ejecutar("INSERT INTO planilla_partido (id_partido, ci_jugador, id_equipo) VALUES (%s,%s,%s)", (id_partido, ci, eq["id_equipo"]), "Jugador agregado a la planilla.")
        return _planilla_accion(id_partido, hacer)

    @app.route("/partidos/<int:id_partido>/planilla/quitar", methods=["POST"])
    @ambos
    def planilla_quitar(id_partido):
        ci = request.form.get("ci_jugador", "")
        def hacer(p):
            tiene = cuenta("SELECT (SELECT COUNT(*) FROM gol WHERE id_partido = %s AND ci_jugador = %s) + (SELECT COUNT(*) FROM tarjeta WHERE id_partido = %s AND ci_jugador = %s)",
                           (id_partido, ci, id_partido, ci))
            if tiene > 0:
                flash("Elimina primero los goles y tarjetas de este jugador antes de quitarlo.", "error")
            else:
                ejecutar("DELETE FROM planilla_partido WHERE id_partido = %s AND ci_jugador = %s", (id_partido, ci), "Jugador quitado de la planilla.")
        return _planilla_accion(id_partido, hacer)

    @app.route("/partidos/<int:id_partido>/gol", methods=["POST"])
    @ambos
    def gol_agregar(id_partido):
        ci, minuto = form_get("ci_jugador", "minuto")
        if not (minuto.isdigit() and 1 <= int(minuto) <= 60):
            flash("El minuto debe estar entre 1 y 60.", "error")
            return redirect(url_for("planilla", id_partido=id_partido))
        return _planilla_accion(id_partido, lambda p: ejecutar("INSERT INTO gol (id_partido, ci_jugador, minuto, autogol) VALUES (%s,%s,%s,%s)",
                                                               (id_partido, ci, int(minuto), 1 if request.form.get("autogol") else 0), "Gol registrado."))

    @app.route("/partidos/<int:id_partido>/gol/eliminar", methods=["POST"])
    @ambos
    def gol_eliminar(id_partido):
        return _planilla_accion(id_partido, lambda p: ejecutar("DELETE FROM gol WHERE id_gol = %s AND id_partido = %s", (request.form.get("id"), id_partido), "Gol eliminado."))

    @app.route("/partidos/<int:id_partido>/tarjeta", methods=["POST"])
    @ambos
    def tarjeta_agregar(id_partido):
        ci, minuto, color = form_get("ci_jugador", "minuto", "color")
        if color not in ("amarilla", "roja") or not (minuto.isdigit() and 1 <= int(minuto) <= 60):
            flash("Datos de tarjeta invalidos.", "error")
            return redirect(url_for("planilla", id_partido=id_partido))

        if color == "roja" and cuenta("SELECT COUNT(*) FROM tarjeta WHERE id_partido = %s AND ci_jugador = %s AND color = 'roja'", (id_partido, ci)) >= 1:
            flash("El jugador ya tiene una tarjeta roja en este partido.", "error")
            return redirect(url_for("planilla", id_partido=id_partido))
        if color == "amarilla" and cuenta("SELECT COUNT(*) FROM tarjeta WHERE id_partido = %s AND ci_jugador = %s AND color = 'amarilla'", (id_partido, ci)) >= 2:
            flash("El jugador ya tiene 2 amarillas en este partido.", "error")
            return redirect(url_for("planilla", id_partido=id_partido))

        def hacer(p):
            if not ejecutar("INSERT INTO tarjeta (id_partido, ci_jugador, minuto, color) VALUES (%s,%s,%s,%s)", (id_partido, ci, int(minuto), color)):
                return
            if color == "roja":
                ejecutar("INSERT INTO sancion_jugador (ci_jugador, id_torneo, motivo, numero_fecha_inicio, cantidad_fechas) VALUES (%s,%s,'roja',%s,1)",
                         (ci, p["id_torneo"], p["numero_fecha"] + 1))
                flash("Tarjeta roja registrada (sancion automatica aplicada).", "ok")
            else:
                total_am = cuenta("SELECT COUNT(*) FROM tarjeta t JOIN partido pt ON pt.id_partido = t.id_partido WHERE t.ci_jugador = %s AND pt.id_torneo = %s AND t.color = 'amarilla'",
                                  (ci, p["id_torneo"]))
                if total_am > 0 and total_am % 3 == 0:
                    ejecutar("INSERT INTO sancion_jugador (ci_jugador, id_torneo, motivo, numero_fecha_inicio, cantidad_fechas) VALUES (%s,%s,'acumulacion de amarillas',%s,1)",
                             (ci, p["id_torneo"], p["numero_fecha"] + 1))
                    flash(f"Amarilla registrada ({total_am} acumuladas). Sancion aplicada por acumulacion.", "ok")
                else:
                    flash(f"Amarilla registrada ({total_am} acumuladas).", "ok")
        return _planilla_accion(id_partido, hacer)

    @app.route("/partidos/<int:id_partido>/tarjeta/eliminar", methods=["POST"])
    @ambos
    def tarjeta_eliminar(id_partido):
        id_t = request.form.get("id")
        def hacer(p):
            t = fila("SELECT ci_jugador, color FROM tarjeta WHERE id_tarjeta = %s AND id_partido = %s", (id_t, id_partido))
            if not t or not ejecutar("DELETE FROM tarjeta WHERE id_tarjeta = %s AND id_partido = %s", (id_t, id_partido)):
                return
            if t["color"] == "roja":
                ejecutar("DELETE FROM sancion_jugador WHERE ci_jugador = %s AND id_torneo = %s AND motivo = 'roja' AND numero_fecha_inicio = %s LIMIT 1",
                         (t["ci_jugador"], p["id_torneo"], p["numero_fecha"] + 1))
            else:
                total_am = cuenta("SELECT COUNT(*) FROM tarjeta t JOIN partido pt ON pt.id_partido = t.id_partido WHERE t.ci_jugador = %s AND pt.id_torneo = %s AND t.color = 'amarilla'",
                                  (t["ci_jugador"], p["id_torneo"]))
                if total_am % 3 == 2:
                    ejecutar("DELETE FROM sancion_jugador WHERE ci_jugador = %s AND id_torneo = %s AND motivo = 'acumulacion de amarillas' ORDER BY id_sancion DESC LIMIT 1",
                             (t["ci_jugador"], p["id_torneo"]))
            flash("Tarjeta eliminada y sancion revertida si correspondia.", "ok")
        return _planilla_accion(id_partido, hacer)
