from datetime import date, datetime, timedelta
from flask import flash, redirect, request, url_for
from db import consulta, ejecutar
from helpers import accion, admin, campo, formulario, form_get, pagina, tabla, validar


def register_torneos_routes(app):
    @app.route("/torneos", methods=["GET", "POST"])
    @admin
    def torneos():
        if request.method == "POST":
            nombre, anio, sem, ini, fin = form_get("nombre", "anio", "semestre", "fecha_inicio", "fecha_fin")
            fechas_ok = False
            try:
                fechas_ok = datetime.strptime(ini, "%Y-%m-%d") <= datetime.strptime(fin, "%Y-%m-%d")
            except ValueError:
                pass

            if validar([
                (nombre and len(nombre) <= 100, "El nombre es obligatorio (maximo 100 caracteres)."),
                (anio.isdigit() and 2020 <= int(anio) <= 2100, "El anio debe estar entre 2020 y 2100."),
                (sem in ("1", "2"), "El semestre debe ser 1 o 2."),
                (fechas_ok, "Las fechas del torneo no son validas o fin es anterior a inicio."),
            ]):
                ejecutar(
                    "INSERT INTO torneo (nombre, anio, semestre, fecha_inicio, fecha_fin) VALUES (%s,%s,%s,%s,%s)",
                    (nombre, int(anio), int(sem), ini, fin),
                    "Torneo creado en etapa de inscripcion.",
                )
            return redirect(url_for("torneos"))

        filas = consulta(
            "SELECT id_torneo AS id, nombre, anio, semestre, fecha_inicio, fecha_fin, estado "
            "FROM torneo ORDER BY anio DESC, semestre DESC"
        )
        for r in filas:
            r["_acciones"] = []
            if r["estado"] == "inscripcion":
                r["_acciones"].append(
                    accion("Pasar a en curso", url_for("torneo_estado", id_torneo=r["id"]),
                           datos={"estado": "en curso"}, confirmar=True)
                )
            elif r["estado"] == "en curso":
                partidos_cant = consulta("SELECT COUNT(*) AS n FROM partido WHERE id_torneo = %s", (r["id"],))
                if partidos_cant and partidos_cant[0]["n"] == 0:
                    r["_acciones"].append(
                        accion("Generar fixture liga", url_for("torneo_generar_fixture", id_torneo=r["id"]),
                               confirmar=True)
                    )
                r["_acciones"].append(
                    accion("Finalizar", url_for("torneo_estado", id_torneo=r["id"]),
                           datos={"estado": "finalizado"}, confirmar=True)
                )

        form = formulario("Nueva edicion del torneo", url_for("torneos"), [
            campo("nombre", "Nombre", extra='required maxlength="100"'),
            campo("anio", "Anio", "number", extra='required min="2020" max="2100"'),
            campo("semestre", "Semestre", "select", [("1", "1"), ("2", "2")]),
            campo("fecha_inicio", "Fecha de inicio", "date", extra="required"),
            campo("fecha_fin", "Fecha de fin", "date", extra="required"),
        ], "Crear torneo")

        return pagina("Torneos", [form],
                      [tabla("Ediciones", ["id", "nombre", "anio", "semestre", "fecha_inicio", "fecha_fin", "estado"],
                             filas, True)])

    @app.route("/torneos/<int:id_torneo>/estado", methods=["POST"])
    @admin
    def torneo_estado(id_torneo):
        nuevo = request.form.get("estado")
        t = consulta("SELECT estado FROM torneo WHERE id_torneo = %s", (id_torneo,))
        transiciones = {"inscripcion": "en curso", "en curso": "finalizado"}

        if not t or transiciones.get(t[0]["estado"]) != nuevo:
            flash("Transicion de estado no permitida (inscripcion -> en curso -> finalizado).", "error")
            return redirect(url_for("torneos"))

        if nuevo == "en curso":
            chicos = consulta(
                "SELECT e.nombre, COUNT(ejt.ci_jugador) AS n FROM equipo e "
                "LEFT JOIN equipo_jugador_torneo ejt ON ejt.id_equipo = e.id_equipo "
                "WHERE e.id_torneo = %s GROUP BY e.id_equipo, e.nombre HAVING n < 5",
                (id_torneo,),
            )
            if chicos:
                flash("Hay equipos con menos de 5 jugadores: " + ", ".join(c["nombre"] for c in chicos), "error")
                return redirect(url_for("torneos"))

        ejecutar("UPDATE torneo SET estado = %s WHERE id_torneo = %s", (nuevo, id_torneo), f"Torneo en estado '{nuevo}'.")
        return redirect(url_for("torneos"))

    @app.route("/torneos/<int:id_torneo>/generar_fixture", methods=["POST"])
    @admin
    def torneo_generar_fixture(id_torneo):
        t = consulta("SELECT * FROM torneo WHERE id_torneo = %s", (id_torneo,))
        if not t or t[0]["estado"] != "en curso":
            flash("Solo se puede generar el fixture para un torneo 'en curso'.", "error")
            return redirect(url_for("torneos"))

        partidos_existentes = consulta("SELECT COUNT(*) AS n FROM partido WHERE id_torneo = %s", (id_torneo,))
        if partidos_existentes and partidos_existentes[0]["n"] > 0:
            flash("El torneo ya tiene partidos creados.", "error")
            return redirect(url_for("torneos"))

        eqs = consulta("SELECT id_equipo FROM equipo WHERE id_torneo = %s ORDER BY id_equipo", (id_torneo,))
        equipos_ids = [e["id_equipo"] for e in eqs]
        if len(equipos_ids) < 2:
            flash("Se necesitan al menos 2 equipos para generar el fixture.", "error")
            return redirect(url_for("torneos"))

        canchas = consulta(
            "SELECT c.nombre_cancha, c.id_complejo FROM cancha c JOIN complejo x ON x.id_complejo = c.id_complejo ORDER BY x.id_complejo, c.nombre_cancha"
        )
        turnos = consulta("SELECT id_turno FROM turno ORDER BY hora_inicio")

        if not canchas or not turnos:
            flash("Debe haber canchas y turnos registrados para armar el fixture.", "error")
            return redirect(url_for("torneos"))

        # Algoritmo Round-Robin (todos contra todos a una rueda)
        es_impar = len(equipos_ids) % 2 != 0
        if es_impar:
            equipos_ids.append(None) # Descanso (bye)

        total_equipos = len(equipos_ids)
        total_fechas = total_equipos - 1
        partidos_por_fecha = total_equipos // 2

        fecha_base = t[0]["fecha_inicio"]
        if isinstance(fecha_base, str):
            fecha_base = datetime.strptime(fecha_base, "%Y-%m-%d").date()

        creados = 0
        for ronda in range(total_fechas):
            num_fecha = ronda + 1
            dia_partido = fecha_base + timedelta(days=ronda * 7)

            # Emparejamientos de la ronda
            slot_idx = 0
            for i in range(partidos_por_fecha):
                local = equipos_ids[i]
                visitante = equipos_ids[total_equipos - 1 - i]

                # Si alguno es el comodín de descanso, no se genera partido
                if local is None or visitante is None:
                    continue

                # Alternar localías
                if ronda % 2 == 1:
                    local, visitante = visitante, local

                # Asignar turno y cancha rotando según slot
                cancha_sel = canchas[slot_idx % len(canchas)]
                turno_sel = turnos[(slot_idx // len(canchas)) % len(turnos)]
                slot_idx += 1

                ejecutar(
                    "INSERT INTO partido (id_torneo, numero_fecha, id_equipo_local, id_equipo_visitante, "
                    "dia, id_turno, nombre_cancha, id_complejo, estado) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'programado')",
                    (id_torneo, num_fecha, local, visitante, dia_partido, turno_sel["id_turno"],
                     cancha_sel["nombre_cancha"], cancha_sel["id_complejo"])
                )
                creados += 1

            # Rotar la lista manteniendo el primer elemento fijo
            equipos_ids = [equipos_ids[0]] + [equipos_ids[-1]] + equipos_ids[1:-1]

        flash(f"Se genero con exito el fixture de {total_fechas} fechas y {creados} partidos (liga a una sola rueda).", "ok")
        return redirect(url_for("partidos"))

