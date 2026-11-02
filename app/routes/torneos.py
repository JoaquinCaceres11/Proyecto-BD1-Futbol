from datetime import datetime
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

