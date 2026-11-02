import os
import mysql.connector
from flask import flash, session

CFG = dict(
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", "3306")),
    database=os.getenv("DB_NAME", "torneo_futbol5"),
)

USUARIOS_DB = {
    "administrador": (
        os.getenv("DB_ADMIN_USER", "app_admin"),
        os.getenv("DB_ADMIN_PASS", "admin_pass_2026"),
    ),
    "planillero": (
        os.getenv("DB_PLANILLERO_USER", "app_planillero"),
        os.getenv("DB_PLANILLERO_PASS", "planillero_pass_2026"),
    ),
}


def conectar(rol=None):
    """Abre conexion a MySQL con el usuario correspondiente al rol."""
    rol_actual = rol or session.get("rol", "planillero")
    usuario, clave = USUARIOS_DB[rol_actual]
    return mysql.connector.connect(user=usuario, password=clave, **CFG)


def consulta(sql, params=None, rol=None):
    """Ejecuta un SELECT y devuelve una lista de diccionarios."""
    con = conectar(rol)
    try:
        cur = con.cursor(dictionary=True)
        cur.execute(sql, params or ())
        return cur.fetchall()
    finally:
        con.close()


def ejecutar(sql, params=None, msj_ok=None):
    """Ejecuta INSERT, UPDATE o DELETE. Flashea mensaje de exito o error de base de datos."""
    con = conectar()
    try:
        cur = con.cursor()
        cur.execute(sql, params or ())
        con.commit()
        if msj_ok:
            flash(msj_ok, "ok")
        return cur.lastrowid if cur.lastrowid else True
    except mysql.connector.Error as e:
        flash(f"No se pudo realizar la operacion: {e.msg}", "error")
        return False
    finally:
        con.close()

