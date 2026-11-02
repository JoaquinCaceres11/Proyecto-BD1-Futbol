"""
Sistema de Gestion del Torneo Interfacultades de Futbol 5 - UCU
Punto de entrada principal de la aplicacion Flask.
"""
import os
from flask import Flask
from routes import register_all_routes

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "cambiar-en-produccion")

# Registrar todos los modulos de rutas del sistema
register_all_routes(app)

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "0") == "1",
    )
