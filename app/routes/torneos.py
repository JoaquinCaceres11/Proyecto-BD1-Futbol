from datetime import date, datetime, timedelta
from flask import flash, redirect, request, url_for
from db import consulta, ejecutar
from helpers import accion, admin, campo, cuenta, fila, formulario, form_get, opciones, pagina, tabla, validar


def register_torneos_routes(app):
    @app.route("/torneos", methods=["GET", "POST"])
    @admin
    def torneos():
        if request.method == "POST":
            nom, anio, sem, ini, fin = form_get("nombre", "anio", "semestre", "fecha_inicio", "fecha_fin")
            fechas_ok = False
            try:
                fechas_ok = datetime.strptime(ini, "%Y-%m-%d") <= datetime.strptime(fin, "%Y-%m-%d")
            except ValueError:
                pass

            if validar([
                (nom and len(nom) <= 100, "Nombre requerido (max 100)."),
                (anio.isdigit() and 2020 <= int(anio) <= 2100, "Anio entre 2020 y 2100."),
                (sem in ("1", "2"), "Semestre 1 o 2."),
                (fechas_ok, "Rango de fechas invalido."),
            ]):
                ejecutar("INSERT INTO torneo (nombre, anio, semestre, fecha_inicio, fecha_fin) VALUES (%s,%s,%s,%s,%s)",
                         (nom, int(anio), int(sem), ini, fin), "Torneo creado en inscripcion.")
            return redirect(url_for("torneos"))

        filas = consulta("SELECT id_torneo AS id, nombre, anio, semestre, fecha_inicio, fecha_fin, estado FROM torneo ORDER BY anio DESC, semestre DESC")
        for r in filas:
            r["_acciones"] = []
            if r["estado"] == "inscripcion":
                r["_acciones"].append(accion("Pasar a en curso", url_for("torneo_estado", id_torneo=r["id"]), datos={"estado": "en curso"}, confirmar=True))
            elif r["estado"] == "en curso":
                if cuenta("SELECT COUNT(*) FROM partido WHERE id_torneo = %s", (r["id"],)) == 0:
                    r["_acciones"].append(accion("Generar fixture liga", url_for("torneo_generar_fixture", id_torneo=r["id"]), confirmar=True))
                r["_acciones"].append(accion("Finalizar", url_for("torneo_estado", id_torneo=r["id"]), datos={"estado": "finalizado"}, confirmar=True))

        form = formulario("Nueva edicion del torneo", url_for("torneos"), [
            campo("nombre", "Nombre", extra='required maxlength="100"'),
            campo("anio", "Anio", "number", extra='required min="2020" max="2100"'),
            campo("semestre", "Semestre", "select", [("1", "1"), ("2", "2")]),
            campo("fecha_inicio", "Fecha de inicio", "date", extra="required"),
            campo("fecha_fin", "Fecha de fin", "date", extra="required"),
        ], "Crear torneo")
        return pagina("Torneos", [form], [tabla("Ediciones", ["id", "nombre", "anio", "semestre", "fecha_inicio", "fecha_fin", "estado"], filas, True)])

    @app.route("/torneos/<int:id_torneo>/estado", methods=["POST"])
    @admin
    def torneo_estado(id_torneo):
        nuevo = request.form.get("estado")
        t = fila("SELECT estado FROM torneo WHERE id_torneo = %s", (id_torneo,))
        transiciones = {"inscripcion": "en curso", "en curso": "finalizado"}
        if not t or transiciones.get(t["estado"]) != nuevo:
            flash("Transicion de estado no permitida.", "error")
        elif nuevo == "en curso" and cuenta("SELECT COUNT(*) FROM equipo e LEFT JOIN equipo_jugador_torneo ejt ON ejt.id_equipo = e.id_equipo WHERE e.id_torneo = %s GROUP BY e.id_equipo HAVING COUNT(ejt.ci_jugador) < 5", (id_torneo,)) > 0:
            flash("Hay equipos con menos de 5 jugadores.", "error")
        elif nuevo == "en curso" and cuenta("SELECT COUNT(*) FROM equipo WHERE id_torneo = %s AND ci_capitan IS NULL", (id_torneo,)) > 0:
            flash("Hay equipos sin capitan designado.", "error")
        else:
            ejecutar("UPDATE torneo SET estado = %s WHERE id_torneo = %s", (nuevo, id_torneo), f"Torneo en estado '{nuevo}'.")
        return redirect(url_for("torneos"))

    @app.route("/torneos/<int:id_torneo>/generar_fixture", methods=["POST"])
    @admin
    def torneo_generar_fixture(id_torneo):
        t = fila("SELECT * FROM torneo WHERE id_torneo = %s", (id_torneo,))
        if not t or t["estado"] != "en curso" or cuenta("SELECT COUNT(*) FROM partido WHERE id_torneo = %s", (id_torneo,)) > 0:
            flash("No se puede generar fixture: el torneo debe estar en curso y sin partidos.", "error")
            return redirect(url_for("torneos"))

        eqs = [e["id_equipo"] for e in consulta("SELECT id_equipo FROM equipo WHERE id_torneo = %s ORDER BY id_equipo", (id_torneo,))]
        canchas = consulta("SELECT c.nombre_cancha, c.id_complejo FROM cancha c JOIN complejo x ON x.id_complejo = c.id_complejo ORDER BY x.id_complejo, c.nombre_cancha")
        turnos = consulta("SELECT id_turno FROM turno ORDER BY hora_inicio")

        if len(eqs) < 2 or not canchas or not turnos:
            flash("Se requieren al menos 2 equipos, canchas y turnos para generar el fixture.", "error")
            return redirect(url_for("torneos"))

        if len(eqs) % 2 != 0:
            eqs.append(None) # Descanso (bye)

        total, fechas = len(eqs), len(eqs) - 1
        base = t["fecha_inicio"] if isinstance(t["fecha_inicio"], date) else datetime.strptime(str(t["fecha_inicio"]), "%Y-%m-%d").date()
        creados = 0

        for r in range(fechas):
            slot = 0
            for i in range(total // 2):
                loc, vis = eqs[i], eqs[total - 1 - i]
                if loc is None or vis is None:
                    continue
                if r % 2 == 1:
                    loc, vis = vis, loc
                c, tur = canchas[slot % len(canchas)], turnos[(slot // len(canchas)) % len(turnos)]
                slot += 1
                ejecutar("INSERT INTO partido (id_torneo, numero_fecha, id_equipo_local, id_equipo_visitante, dia, id_turno, nombre_cancha, id_complejo) "
                         "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)", (id_torneo, r + 1, loc, vis, base + timedelta(days=r * 7), tur["id_turno"], c["nombre_cancha"], c["id_complejo"]))
                creados += 1
            eqs = [eqs[0]] + [eqs[-1]] + eqs[1:-1]

        flash(f"Fixture generado: {fechas} fechas y {creados} partidos (liga a una sola rueda).", "ok")
        return redirect(url_for("partidos"))
