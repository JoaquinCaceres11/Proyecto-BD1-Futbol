import mysql.connector
from flask import flash, redirect, render_template, request, session, url_for
from db import consulta
from helpers import EMAIL_RE, ambos, form_get


def register_auth_routes(app):
    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            correo, clave = form_get("correo", "contrasenia")
            if not EMAIL_RE.match(correo) or not clave:
                flash("Ingresa un correo valido y la contrasenia.", "error")
            else:
                try:
                    r = consulta(
                        "SELECT rol FROM login WHERE correo = %s AND contrasenia = SHA2(%s, 256)",
                        (correo, clave),
                        rol="administrador",
                    )
                except mysql.connector.Error as e:
                    flash(f"Error de conexion con la base de datos: {e.msg}", "error")
                    r = None

                if r:
                    session["rol"], session["correo"] = r[0]["rol"], correo
                    return redirect(url_for("inicio"))
                if r is not None:
                    flash("Credenciales incorrectas.", "error")

        return render_template("login.html")

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))

    @app.route("/salud")
    def salud():
        return "ok"

    @app.route("/")
    @ambos
    def inicio():
        return render_template("inicio.html")

