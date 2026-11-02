from flask import redirect, request, url_for
from db import consulta, ejecutar
from helpers import SUPERFICIES, accion, admin, campo, formulario, form_get, opciones, pagina, tabla, validar


def register_complejos_routes(app):
    @app.route("/complejos", methods=["GET", "POST"])
    @admin
    def complejos():
        if request.method == "POST":
            nom, dir_, depto = form_get("nombre", "direccion", "departamento")
            if validar([
                (nom and len(nom) <= 100, "El nombre del complejo es obligatorio (maximo 100 caracteres)."),
                (dir_ and len(dir_) <= 150, "La direccion es obligatoria (maximo 150 caracteres)."),
                (depto and len(depto) <= 50, "El departamento es obligatorio (maximo 50 caracteres)."),
            ]):
                ejecutar(
                    "INSERT INTO complejo (nombre, direccion, departamento) VALUES (%s,%s,%s)",
                    (nom, dir_, depto),
                    "Complejo creado.",
                )
            return redirect(url_for("complejos"))

        comp = consulta("SELECT id_complejo AS id, nombre, direccion, departamento FROM complejo ORDER BY nombre")
        for r in comp:
            r["_acciones"] = [accion("Eliminar", url_for("complejo_eliminar", id_complejo=r["id"]), confirmar=True)]

        can = consulta(
            "SELECT c.nombre_cancha AS cancha, c.id_complejo, x.nombre AS complejo, c.superficie, "
            "IF(c.techada, 'Si', 'No') AS techada FROM cancha c "
            "JOIN complejo x ON x.id_complejo = c.id_complejo ORDER BY x.nombre, c.nombre_cancha"
        )
        for r in can:
            r["_acciones"] = [accion("Eliminar", url_for("cancha_eliminar"), confirmar=True,
                                     datos={"nombre_cancha": r["cancha"], "id_complejo": r["id_complejo"]})]

        f1 = formulario("Nuevo complejo", url_for("complejos"), [
            campo("nombre", "Nombre", extra='required maxlength="100"'),
            campo("direccion", "Direccion", extra='required maxlength="150"'),
            campo("departamento", "Departamento", extra='required maxlength="50"'),
        ], "Crear complejo")

        f2 = formulario("Nueva cancha", url_for("cancha_crear"), [
            campo("id_complejo", "Complejo", "select", opciones("SELECT id_complejo AS valor, nombre AS texto FROM complejo ORDER BY nombre")),
            campo("nombre_cancha", "Nombre de la cancha", extra='required maxlength="50"'),
            campo("superficie", "Superficie", "select", [(s, s) for s in SUPERFICIES]),
            campo("techada", "Techada", "checkbox"),
        ], "Crear cancha")

        return pagina("Complejos y canchas", [f1, f2],
                      [tabla("Complejos", ["id", "nombre", "direccion", "departamento"], comp, True),
                       tabla("Canchas", ["cancha", "complejo", "superficie", "techada"], can, True)])

    @app.route("/complejos/<int:id_complejo>/eliminar", methods=["POST"])
    @admin
    def complejo_eliminar(id_complejo):
        ejecutar("DELETE FROM complejo WHERE id_complejo = %s", (id_complejo,), "Complejo eliminado.")
        return redirect(url_for("complejos"))

    @app.route("/canchas/crear", methods=["POST"])
    @admin
    def cancha_crear():
        nombre, id_c, sup = form_get("nombre_cancha", "id_complejo", "superficie")
        if validar([
            (nombre and len(nombre) <= 50, "El nombre de la cancha es obligatorio (maximo 50 caracteres)."),
            (id_c.isdigit(), "Selecciona un complejo."),
            (sup in SUPERFICIES, "Superficie invalida."),
        ]):
            ejecutar(
                "INSERT INTO cancha (nombre_cancha, id_complejo, superficie, techada) VALUES (%s,%s,%s,%s)",
                (nombre, int(id_c), sup, 1 if request.form.get("techada") else 0),
                "Cancha creada.",
            )
        return redirect(url_for("complejos"))

    @app.route("/canchas/eliminar", methods=["POST"])
    @admin
    def cancha_eliminar():
        ejecutar(
            "DELETE FROM cancha WHERE nombre_cancha = %s AND id_complejo = %s",
            (request.form.get("nombre_cancha"), request.form.get("id_complejo")),
            "Cancha eliminada.",
        )
        return redirect(url_for("complejos"))

