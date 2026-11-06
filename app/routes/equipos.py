from flask import flash, redirect, request, url_for
from db import consulta, ejecutar
from helpers import CI_RE, accion, admin, campo, cuenta, fila, formulario, form_get, opciones, pagina, tabla, validar


def register_equipos_routes(app):
    @app.route("/equipos", methods=["GET", "POST"])
    @admin
    def equipos():
        if request.method == "POST":
            nom, id_t, id_f = form_get("nombre", "id_torneo", "id_facultad")
            t = fila("SELECT estado FROM torneo WHERE id_torneo = %s", (id_t,)) if id_t.isdigit() else None
            if validar([
                (nom and len(nom) <= 100, "Nombre requerido (max 100)."),
                (id_t.isdigit() and id_f.isdigit(), "Selecciona torneo y facultad."),
                (t and t["estado"] == "inscripcion", "Solo se pueden crear equipos en etapa de inscripcion."),
            ]):
                ejecutar("INSERT INTO equipo (nombre, id_torneo, id_facultad) VALUES (%s,%s,%s)", (nom, int(id_t), int(id_f)), "Equipo creado.")
            return redirect(url_for("equipos"))

        filas = consulta(
            "SELECT e.id_equipo AS id, e.nombre, t.nombre AS torneo, f.nombre AS facultad, "
            "CONCAT(c.apellido, ', ', c.nombre) AS capitan, "
            "(SELECT COUNT(*) FROM equipo_jugador_torneo x WHERE x.id_equipo = e.id_equipo) AS jugadores "
            "FROM equipo e JOIN torneo t ON t.id_torneo = e.id_torneo JOIN facultad f ON f.id_facultad = e.id_facultad "
            "LEFT JOIN jugador c ON c.ci = e.ci_capitan ORDER BY t.anio DESC, t.semestre DESC, e.nombre"
        )
        for r in filas:
            r["_acciones"] = [accion("Plantel", url_for("equipo_plantel", id_equipo=r["id"]), "get"),
                              accion("Modificar", url_for("equipo_editar", id_equipo=r["id"]), "get"),
                              accion("Eliminar", url_for("equipo_eliminar", id_equipo=r["id"]), confirmar=True)]

        torneos_op = opciones("SELECT id_torneo AS valor, CONCAT(nombre, ' (', estado, ')') AS texto FROM torneo ORDER BY anio DESC, semestre DESC")
        if not torneos_op:
            torneos_op = [("", "-- No hay torneos registrados --")]

        form = formulario("Nuevo equipo", url_for("equipos"), [
            campo("nombre", "Nombre del equipo", extra='required maxlength="100"'),
            campo("id_torneo", "Torneo", "select", torneos_op),
            campo("id_facultad", "Facultad", "select", opciones("SELECT id_facultad AS valor, nombre AS texto FROM facultad ORDER BY nombre")),
        ], "Crear equipo")
        return pagina("Equipos", [form], [tabla("Equipos inscriptos", ["id", "nombre", "torneo", "facultad", "capitan", "jugadores"], filas, True)])

    
    @app.route("/equipos/<int:id_equipo>/editar", methods=["GET", "POST"])
    @admin
    def equipo_editar(id_equipo):
        eq = fila("SELECT * FROM equipo WHERE id_equipo = %s", (id_equipo,))
        if not eq:
            flash("El equipo no existe.", "error")
            return redirect(url_for("equipos"))

        if request.method == "POST":
            nom = form_get("nombre")[0]
            if validar([(nom and len(nom) <= 100, "Nombre requerido (max 100).")]):
                ejecutar("UPDATE equipo SET nombre = %s WHERE id_equipo = %s", (nom, id_equipo), "Equipo modificado.")
                return redirect(url_for("equipos"))
            return redirect(url_for("equipo_editar", id_equipo=id_equipo))

        form = formulario("Modificar equipo", url_for("equipo_editar", id_equipo=id_equipo), [
            campo("nombre", "Nombre del equipo", extra='required maxlength="100"', valor=eq["nombre"]),
        ], "Guardar cambios")
        return pagina(f"Modificar equipo {eq['nombre']}", [form])

    @app.route("/equipos/<int:id_equipo>/camiseta", methods=["POST"])
    @admin
    def plantel_camiseta(id_equipo):
        eq = fila("SELECT t.estado FROM equipo e JOIN torneo t ON t.id_torneo = e.id_torneo WHERE e.id_equipo = %s", (id_equipo,))
        ci, num = form_get("ci_jugador", "numero_camiseta")
        if validar([
            (eq and eq["estado"] == "inscripcion", "Solo se puede modificar el plantel en inscripcion."),
            (num.isdigit() and 1 <= int(num) <= 99, "La camiseta debe estar entre 1 y 99."),
            (cuenta("SELECT COUNT(*) FROM equipo_jugador_torneo WHERE id_equipo = %s AND numero_camiseta = %s AND ci_jugador <> %s",
                    (id_equipo, num if num.isdigit() else 0, ci)) == 0, "Esa camiseta ya esta en uso en el equipo."),
        ]):
            ejecutar("UPDATE equipo_jugador_torneo SET numero_camiseta = %s WHERE id_equipo = %s AND ci_jugador = %s",
                     (int(num), id_equipo, ci), "Camiseta modificada.")
        return redirect(url_for("equipo_plantel", id_equipo=id_equipo))
    
    
    @app.route("/equipos/<int:id_equipo>/eliminar", methods=["POST"])
    @admin
    def equipo_eliminar(id_equipo):
        if cuenta("SELECT COUNT(*) FROM partido WHERE id_equipo_local = %s OR id_equipo_visitante = %s", (id_equipo, id_equipo)) > 0:
            flash("No se puede eliminar un equipo con partidos asignados.", "error")
        else:
            ejecutar("DELETE FROM equipo WHERE id_equipo = %s", (id_equipo,), "Equipo eliminado.")
        return redirect(url_for("equipos"))

    @app.route("/equipos/<int:id_equipo>", methods=["GET", "POST"])
    @admin
    def equipo_plantel(id_equipo):
        eq = fila("SELECT e.*, t.estado AS estado_torneo, f.nombre AS facultad FROM equipo e "
                  "JOIN torneo t ON t.id_torneo = e.id_torneo JOIN facultad f ON f.id_facultad = e.id_facultad WHERE e.id_equipo = %s", (id_equipo,))
        if not eq:
            flash("El equipo no existe.", "error")
            return redirect(url_for("equipos"))

        if request.method == "POST":
            ci, num = form_get("ci_jugador", "numero_camiseta")
            jug = fila("SELECT id_facultad, tipo FROM jugador WHERE ci = %s", (ci,)) if CI_RE.match(ci) else None
            staff = jug and jug["tipo"] in ("docente", "funcionario")
            cant_staff = cuenta("SELECT COUNT(*) FROM equipo_jugador_torneo ejt JOIN jugador j ON j.ci = ejt.ci_jugador WHERE ejt.id_equipo = %s AND j.tipo IN ('docente','funcionario')", (id_equipo,))

            if validar([
                (eq["estado_torneo"] == "inscripcion", "Solo se puede modificar el plantel en inscripcion."),
                (CI_RE.match(ci) and num.isdigit() and 1 <= int(num) <= 99, "Datos invalidos."),
                (jug and jug["id_facultad"] == eq["id_facultad"], "El jugador debe ser de la facultad del equipo."),
                (cuenta("SELECT COUNT(*) FROM equipo_jugador_torneo WHERE id_equipo = %s", (id_equipo,)) < 10, "El plantel ya tiene 10 jugadores."),
                (not staff or cant_staff < 2, "Maximo 2 docentes/funcionarios por plantel."),
            ]):
                ejecutar("INSERT INTO equipo_jugador_torneo (id_equipo, ci_jugador, id_torneo, numero_camiseta) VALUES (%s,%s,%s,%s)",
                         (id_equipo, ci, eq["id_torneo"], int(num)), "Jugador agregado al plantel.")
            return redirect(url_for("equipo_plantel", id_equipo=id_equipo))

        filas = consulta(
            "SELECT j.ci, CONCAT(j.apellido, ', ', j.nombre) AS jugador, j.tipo, ejt.numero_camiseta AS camiseta, "
            "IF(e.ci_capitan = j.ci, 'Si', '') AS capitan FROM equipo_jugador_torneo ejt "
            "JOIN jugador j ON j.ci = ejt.ci_jugador JOIN equipo e ON e.id_equipo = ejt.id_equipo "
            "WHERE ejt.id_equipo = %s ORDER BY ejt.numero_camiseta", (id_equipo,)
        )
        for r in filas:
            r["_acciones"] = [accion("Hacer capitan", url_for("equipo_capitan", id_equipo=id_equipo), datos={"ci_jugador": r["ci"]}),
                              accion("Quitar", url_for("plantel_quitar", id_equipo=id_equipo), datos={"ci_jugador": r["ci"]}, confirmar=True)]

        disp = opciones("SELECT j.ci AS valor, CONCAT(j.apellido, ', ', j.nombre, ' (', j.tipo, ')') AS texto "
                        "FROM jugador j WHERE j.id_facultad = %s AND j.ci NOT IN (SELECT ci_jugador FROM equipo_jugador_torneo WHERE id_torneo = %s) ORDER BY j.apellido",
                        (eq["id_facultad"], eq["id_torneo"]))
        form = formulario("Agregar jugador al plantel", url_for("equipo_plantel", id_equipo=id_equipo), [
            campo("ci_jugador", "Jugador", "select", disp),
            campo("numero_camiseta", "Numero de camiseta", "number", extra='required min="1" max="99"'),
        ], "Agregar")

        es_insc = eq["estado_torneo"] == "inscripcion"
        jugadores_op = [(r["ci"], f"{r['jugador']} (camiseta {r['camiseta']})") for r in filas]
        form_cam = formulario("Cambiar camiseta", url_for("plantel_camiseta", id_equipo=id_equipo), [
            campo("ci_jugador", "Jugador", "select", jugadores_op),
            campo("numero_camiseta", "Nuevo numero", "number", extra='required min="1" max="99"'),
        ], "Cambiar")
        return pagina(f"Plantel de {eq['nombre']}", [form, form_cam] if es_insc else [],
                      [tabla(f"Plantel ({len(filas)} jugadores, 5 a 10, max. 2 staff)", ["ci", "jugador", "tipo", "camiseta", "capitan"], filas, es_insc)],
                      subtitulo=f"Facultad: {eq['facultad']} - Estado: {eq['estado_torneo']}")

    @app.route("/equipos/<int:id_equipo>/capitan", methods=["POST"])
    @admin
    def equipo_capitan(id_equipo):
        ci = request.form.get("ci_jugador", "")
        if cuenta("SELECT COUNT(*) FROM equipo_jugador_torneo WHERE id_equipo = %s AND ci_jugador = %s", (id_equipo, ci)) == 0:
            flash("El capitan debe ser jugador del plantel.", "error")
        else:
            ejecutar("UPDATE equipo SET ci_capitan = %s WHERE id_equipo = %s", (ci, id_equipo), "Capitan actualizado.")
        return redirect(url_for("equipo_plantel", id_equipo=id_equipo))

    @app.route("/equipos/<int:id_equipo>/quitar", methods=["POST"])
    @admin
    def plantel_quitar(id_equipo):
        eq = fila("SELECT e.ci_capitan, t.estado AS estado_torneo FROM equipo e JOIN torneo t ON t.id_torneo = e.id_torneo WHERE e.id_equipo = %s", (id_equipo,))
        ci = request.form.get("ci_jugador", "")
        if not eq or eq["estado_torneo"] != "inscripcion":
            flash("Solo se puede modificar el plantel en inscripcion.", "error")
        elif eq["ci_capitan"] == ci:
            flash("No se puede quitar al capitan: designa otro primero.", "error")
        else:
            ejecutar("DELETE FROM equipo_jugador_torneo WHERE id_equipo = %s AND ci_jugador = %s", (id_equipo, ci), "Jugador quitado del plantel.")
        return redirect(url_for("equipo_plantel", id_equipo=id_equipo))
