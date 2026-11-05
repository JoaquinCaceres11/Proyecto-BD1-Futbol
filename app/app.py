"""
Sistema de Gestion del Torneo Interfacultades de Futbol 5 - UCU
Punto de entrada principal de la aplicacion Flask.
"""
import os
import secrets
from flask import Flask, abort, request, session
from routes import register_all_routes

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "cambiar-en-produccion")


def generar_csrf_token():
    """Genera y devuelve un token CSRF almacenado en la sesion."""
    if "_csrf_token" not in session:
        session["_csrf_token"] = secrets.token_hex(32)
    return session["_csrf_token"]


app.jinja_env.globals["csrf_token"] = generar_csrf_token

RUTAS_EXENTAS_CSRF = ("/login", "/salud")


@app.before_request
def proteger_csrf():
    """Verifica el token CSRF en todos los POST, excepto login y healthcheck."""
    if request.method == "POST":
        if request.path not in RUTAS_EXENTAS_CSRF:
            token = session.get("_csrf_token")
            if not token or token != request.form.get("_csrf_token"):
                abort(403)


# Registrar todos los modulos de rutas del sistema
register_all_routes(app)

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "0") == "1",
    )
