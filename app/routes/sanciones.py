from flask import redirect, request, url_for
from db import consulta, ejecutar
from helpers import CI_RE, accion, admin, campo, formulario, form_get, opciones, pagina, tabla, validar


def register_sanciones_routes(app):
    @app.route("/sanciones", methods=["GET", "POST"])
    @admin
    def sanciones():
        if request.method == "POST":
            ci, id_t, ini, cant = form_get("ci_jugador", "id_torneo", "numero_fecha_inicio", "cantidad_fechas")

            if validar([
                (CI_RE.match(ci) and id_t.isdigit(), "Selecciona jugador y torneo."),
                (ini.isdigit() and int(ini) >= 1, "La fecha de inicio debe ser un numero mayor o igual a 1."),
                (cant.isdigit() and 1 <= int(cant) <= 20, "La cantidad de fechas debe estar entre 1 y 20."),
            ]):
                ejecutar(
                    "INSERT INTO sancion_jugador (ci_jugador, id_torneo, motivo, numero_fecha_inicio, cantidad_fechas) "
                    "VALUES (%s,%s,'disciplinaria',%s,%s)",
                    (ci, int(id_t), int(ini), int(cant)),
                    "Sancion disciplinaria registrada.",
                )
            return redirect(url_for("sanciones"))

        filas = consulta(
            "SELECT s.id_sancion AS id, CONCAT(j.apellido, ', ', j.nombre) AS jugador, t.nombre AS torneo, s.motivo, "
            "s.numero_fecha_inicio AS desde_fecha, s.cantidad_fechas AS cantidad_fechas "
            "FROM sancion_jugador s JOIN jugador j ON j.ci = s.ci_jugador JOIN torneo t ON t.id_torneo = s.id_torneo "
            "ORDER BY s.id_torneo, s.numero_fecha_inicio"
        )
        for r in filas:
            r["_acciones"] = [accion("Eliminar", url_for("sancion_eliminar", id_sancion=r["id"]), confirmar=True)]

        jugadores_op = opciones(
            "SELECT j.ci AS valor, CONCAT(j.apellido, ', ', j.nombre, ' (CI: ', j.ci, ')') AS texto "
            "FROM jugador j ORDER BY j.apellido, j.nombre"
        )
        torneos_op = opciones("SELECT id_torneo AS valor, CONCAT(nombre, ' (', estado, ')') AS texto FROM torneo ORDER BY anio DESC, semestre DESC")

        form = formulario("Nueva sancion disciplinaria", url_for("sanciones"), [
            campo("ci_jugador", "Jugador", "select", jugadores_op),
            campo("id_torneo", "Torneo", "select", torneos_op),
            campo("numero_fecha_inicio", "Desde la fecha", "number", extra='required min="1"'),
            campo("cantidad_fechas", "Cantidad de fechas", "number", extra='required min="1" max="20"'),
        ], "Aplicar sancion")

        return pagina("Sanciones", [form],
                      [tabla("Sanciones (las de roja y amarillas se generan automaticamente)",
                             ["id", "jugador", "torneo", "motivo", "desde_fecha", "cantidad_fechas"], filas, True)])

    @app.route("/sanciones/<int:id_sancion>/eliminar", methods=["POST"])
    @admin
    def sancion_eliminar(id_sancion):
        ejecutar("DELETE FROM sancion_jugador WHERE id_sancion = %s", (id_sancion,), "Sancion eliminada.")
        return redirect(url_for("sanciones"))

