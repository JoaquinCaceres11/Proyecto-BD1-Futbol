from flask import flash, redirect, request, url_for
from db import consulta, ejecutar
from helpers import CI_RE, accion, admin, campo, formulario, form_get, opciones, pagina, tabla, validar


def register_equipos_routes(app):
    @app.route("/equipos", methods=["GET", "POST"])
    @admin
    def equipos():
        if request.method == "POST":
            nombre, id_t, id_f = form_get("nombre", "id_torneo", "id_facultad")
            t = consulta("SELECT estado FROM torneo WHERE id_torneo = %s", (id_t,)) if id_t.isdigit() else []
            if validar([
                (nombre and len(nombre) <= 100, "El nombre del equipo es obligatorio (maximo 100 caracteres)."),
                (id_t.isdigit() and id_f.isdigit(), "Selecciona torneo y facultad."),
                (t and t[0]["estado"] == "inscripcion", "Solo se pueden crear equipos en etapa de inscripcion."),
            ]):
                ejecutar(
                    "INSERT INTO equipo (nombre, id_torneo, id_facultad) VALUES (%s,%s,%s)",
                    (nombre, int(id_t), int(id_f)),
                    "Equipo creado. Ahora cargale el plantel.",
                )
            return redirect(url_for("equipos"))

        filas = consulta(
            "SELECT e.id_equipo AS id, e.nombre, t.nombre AS torneo, f.nombre AS facultad, "
            "CONCAT(c.apellido, ', ', c.nombre) AS capitan, "
            "(SELECT COUNT(*) FROM equipo_jugador_torneo x WHERE x.id_equipo = e.id_equipo) AS jugadores "
            "FROM equipo e JOIN torneo t ON t.id_torneo = e.id_torneo JOIN facultad f ON f.id_facultad = e.id_facultad "
            "LEFT JOIN jugador c ON c.ci = e.ci_capitan ORDER BY t.anio DESC, t.semestre DESC, e.nombre"
        )
        for r in filas:
            r["_acciones"] = [
                accion("Plantel", url_for("equipo_plantel", id_equipo=r["id"]), "get"),
                accion("Eliminar", url_for("equipo_eliminar", id_equipo=r["id"]), confirmar=True),
            ]

        form = formulario("Nuevo equipo", url_for("equipos"), [
            campo("nombre", "Nombre del equipo", extra='required maxlength="100"'),
            campo("id_torneo", "Torneo", "select", opciones("SELECT id_torneo AS valor, nombre AS texto FROM torneo WHERE estado = 'inscripcion'")),
            campo("id_facultad", "Facultad", "select", opciones("SELECT id_facultad AS valor, nombre AS texto FROM facultad ORDER BY nombre")),
        ], "Crear equipo")

        return pagina("Equipos", [form],
                      [tabla("Equipos inscriptos", ["id", "nombre", "torneo", "facultad", "capitan", "jugadores"], filas, True)])

    @app.route("/equipos/<int:id_equipo>/eliminar", methods=["POST"])
    @admin
    def equipo_eliminar(id_equipo):
        partidos = consulta(
            "SELECT COUNT(*) AS n FROM partido WHERE id_equipo_local = %s OR id_equipo_visitante = %s",
            (id_equipo, id_equipo))
        if partidos and partidos[0]["n"] > 0:
            flash("No se puede eliminar un equipo que tiene partidos programados o jugados.", "error")
            return redirect(url_for("equipos"))
        ejecutar("DELETE FROM equipo WHERE id_equipo = %s", (id_equipo,), "Equipo eliminado.")
        return redirect(url_for("equipos"))

    @app.route("/equipos/<int:id_equipo>", methods=["GET", "POST"])
    @admin
    def equipo_plantel(id_equipo):
        eq = consulta(
            "SELECT e.*, t.estado AS estado_torneo, f.nombre AS facultad FROM equipo e "
            "JOIN torneo t ON t.id_torneo = e.id_torneo JOIN facultad f ON f.id_facultad = e.id_facultad WHERE e.id_equipo = %s",
            (id_equipo,),
        )
        if not eq:
            flash("El equipo no existe.", "error")
            return redirect(url_for("equipos"))
        eq = eq[0]

        if request.method == "POST":
            ci, camiseta = form_get("ci_jugador", "numero_camiseta")
            if validar([
                (CI_RE.match(ci), "Selecciona un jugador."),
                (camiseta.isdigit() and 1 <= int(camiseta) <= 99, "La camiseta debe ser un numero entre 1 y 99."),
            ]):
                ejecutar(
                    "INSERT INTO equipo_jugador_torneo (id_equipo, ci_jugador, id_torneo, numero_camiseta) VALUES (%s,%s,%s,%s)",
                    (id_equipo, ci, eq["id_torneo"], int(camiseta)),
                    "Jugador agregado al plantel.",
                )
            return redirect(url_for("equipo_plantel", id_equipo=id_equipo))

        filas = consulta(
            "SELECT j.ci, CONCAT(j.apellido, ', ', j.nombre) AS jugador, j.tipo, ejt.numero_camiseta AS camiseta, "
            "IF(e.ci_capitan = j.ci, 'Si', '') AS capitan FROM equipo_jugador_torneo ejt "
            "JOIN jugador j ON j.ci = ejt.ci_jugador JOIN equipo e ON e.id_equipo = ejt.id_equipo "
            "WHERE ejt.id_equipo = %s ORDER BY ejt.numero_camiseta",
            (id_equipo,),
        )
        for r in filas:
            r["_acciones"] = [
                accion("Hacer capitan", url_for("equipo_capitan", id_equipo=id_equipo), datos={"ci_jugador": r["ci"]}),
                accion("Quitar", url_for("plantel_quitar", id_equipo=id_equipo), datos={"ci_jugador": r["ci"]}, confirmar=True),
            ]

        disponibles = opciones(
            "SELECT j.ci AS valor, CONCAT(j.apellido, ', ', j.nombre, ' (', j.tipo, ')') AS texto "
            "FROM jugador j WHERE j.id_facultad = %s AND j.ci NOT IN "
            "(SELECT ci_jugador FROM equipo_jugador_torneo WHERE id_torneo = %s) ORDER BY j.apellido",
            (eq["id_facultad"], eq["id_torneo"]),
        )
        form = formulario("Agregar jugador al plantel", url_for("equipo_plantel", id_equipo=id_equipo), [
            campo("ci_jugador", "Jugador (de la facultad del equipo)", "select", disponibles),
            campo("numero_camiseta", "Numero de camiseta", "number", extra='required min="1" max="99"'),
        ], "Agregar")

        es_inscripcion = eq["estado_torneo"] == "inscripcion"
        return pagina(
            f"Plantel de {eq['nombre']}",
            [form] if es_inscripcion else [],
            [tabla(f"Plantel ({len(filas)} jugadores, entre 5 y 10, max. 2 docentes/funcionarios)",
                   ["ci", "jugador", "tipo", "camiseta", "capitan"], filas, es_inscripcion)],
            subtitulo=f"Facultad: {eq['facultad']} - Torneo en estado: {eq['estado_torneo']}",
        )

    @app.route("/equipos/<int:id_equipo>/capitan", methods=["POST"])
    @admin
    def equipo_capitan(id_equipo):
        ejecutar("UPDATE equipo SET ci_capitan = %s WHERE id_equipo = %s", (request.form.get("ci_jugador", ""), id_equipo), "Capitan actualizado.")
        return redirect(url_for("equipo_plantel", id_equipo=id_equipo))

    @app.route("/equipos/<int:id_equipo>/quitar", methods=["POST"])
    @admin
    def plantel_quitar(id_equipo):
        ci = request.form.get("ci_jugador", "")
        cap = consulta("SELECT ci_capitan FROM equipo WHERE id_equipo = %s", (id_equipo,))
        if cap and cap[0]["ci_capitan"] == ci:
            flash("No se puede quitar al capitan: designa otro capitan primero.", "error")
        else:
            ejecutar("DELETE FROM equipo_jugador_torneo WHERE id_equipo = %s AND ci_jugador = %s", (id_equipo, ci), "Jugador quitado del plantel.")
        return redirect(url_for("equipo_plantel", id_equipo=id_equipo))

