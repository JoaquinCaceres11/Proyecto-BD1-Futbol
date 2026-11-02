import re
from functools import wraps
from flask import flash, redirect, render_template, request, session, url_for
from db import consulta

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$")
CI_RE = re.compile(r"^\d{7,8}$")
TIPOS = ["grado", "posgrado", "docente", "funcionario"]
SUPERFICIES = ["sintetico", "parquet"]
CAMPOS_JUGADOR = ["ci", "nombre", "apellido", "email", "fecha_nacimiento", "id_facultad", "tipo"]


# ---------------------------------------------------------------------
# Permisos y seguridad
# ---------------------------------------------------------------------
def requiere_rol(*roles):
    """Restringe una ruta a uno o varios roles (administrador, planillero)."""
    def decorador(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if "rol" not in session:
                return redirect(url_for("login"))
            if session["rol"] not in roles:
                flash("No tenes permisos para acceder a esa seccion.", "error")
                return redirect(url_for("inicio"))
            return f(*args, **kwargs)
        return wrapper
    return decorador


admin = requiere_rol("administrador")
ambos = requiere_rol("administrador", "planillero")


# ---------------------------------------------------------------------
# Utilitarios de formularios y validaciones
# ---------------------------------------------------------------------
def form_get(*keys):
    """Obtiene valores del formulario HTTP limpios de espacios."""
    return [request.form.get(k, "").strip() for k in keys]


def validar(reglas):
    """
    Evalua una lista de tuplas: (condicion, mensaje_error).
    Si alguna condicion es falsa, muestra el mensaje como flash error.
    Devuelve True si todas las condiciones fueron verdaderas.
    """
    errores = [msj for condicion, msj in reglas if not condicion]
    for e in errores:
        flash(e, "error")
    return not errores


# ---------------------------------------------------------------------
# Helpers de presentacion (usados por templates/pagina.html)
# ---------------------------------------------------------------------
def campo(name, label, tipo="text", opciones=None, valor="", extra=""):
    return dict(name=name, label=label, tipo=tipo, opciones=opciones or [], valor=valor, extra=extra)


def accion(label, url, metodo="post", datos=None, confirmar=False):
    return dict(label=label, url=url, metodo=metodo, datos=datos or {}, confirmar=confirmar)


def formulario(titulo, action, campos, boton="Guardar"):
    return dict(titulo=titulo, action=action, campos=campos, boton=boton)


def tabla(titulo, columnas, filas, con_acciones=False):
    return dict(titulo=titulo, columnas=columnas, filas=filas, con_acciones=con_acciones)


def pagina(titulo, formularios=None, tablas=None, subtitulo=None):
    return render_template(
        "pagina.html",
        titulo=titulo,
        subtitulo=subtitulo,
        formularios=formularios or [],
        tablas=tablas or [],
    )


def opciones(sql, params=None):
    """Genera lista de tuplas (valor, texto) a partir de una consulta SQL."""
    return [(r["valor"], r["texto"]) for r in consulta(sql, params)]

