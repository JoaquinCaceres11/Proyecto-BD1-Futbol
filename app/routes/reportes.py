import os
import re
import mysql.connector
from flask import flash, redirect, render_template, request, url_for
from db import consulta
from helpers import accion, admin, opciones, pagina, tabla

_AQUI = os.path.dirname(os.path.abspath(__file__))
_CANDIDATAS = [
    os.path.join(_AQUI, "..", "sql", "03_reportes.sql"),
    os.path.join(_AQUI, "..", "..", "sql", "03_reportes.sql"),
]
RUTA_REPORTES = os.getenv("REPORTES_SQL") or next((p for p in _CANDIDATAS if os.path.exists(p)), _CANDIDATAS[0])


def cargar_reportes():
    with open(RUTA_REPORTES, encoding="utf-8") as fh:
        texto = fh.read()
    reportes = []
    for bloque in texto.split(";"):
        titulo, lineas = None, []
        for linea in bloque.splitlines():
            s = linea.strip()
            m = re.match(r"^--\s*(R\d+.*)$", s)
            if m:
                titulo = m.group(1)
            elif s and not s.startswith("--") and not s.upper().startswith("USE "):
                lineas.append(linea)
        if titulo and lineas:
            sql = "\n".join(lineas)
            sql = re.sub(r"id_torneo\s*=\s*1\b", "id_torneo = %(t)s", sql)
            sql = re.sub(r"\b4\s*(>=|<)\s+s\.", r"%(f)s \1 s.", sql)
            reportes.append((titulo, sql))
    return reportes


def register_reportes_routes(app):
    @app.route("/reportes")
    @admin
    def reportes():
        filas = [
            {"reporte": t, "_acciones": [accion("Ver", url_for("reporte", n=i), "get")]}
            for i, (t, _) in enumerate(cargar_reportes())
        ]
        return pagina("Reportes", [], [tabla("Reportes disponibles", ["reporte"], filas, True)])

    @app.route("/reportes/<int:n>")
    @admin
    def reporte(n):
        lista = cargar_reportes()
        if not 0 <= n < len(lista):
            flash("Reporte inexistente.", "error")
            return redirect(url_for("reportes"))

        titulo, sql = lista[n]
        t = request.args.get("torneo", "1")
        f = request.args.get("fecha", "4")
        if not (t.isdigit() and f.isdigit()):
            flash("Parametros invalidos.", "error")
            return redirect(url_for("reportes"))

        try:
            filas = consulta(sql, {"t": int(t), "f": int(f)})
        except mysql.connector.Error as e:
            flash(f"Error ejecutando el reporte: {e.msg}", "error")
            return redirect(url_for("reportes"))

        columnas = list(filas[0].keys()) if filas else []
        torneos_ = opciones("SELECT id_torneo AS valor, nombre AS texto FROM torneo ORDER BY id_torneo")
        return render_template(
            "reporte.html",
            titulo=titulo,
            columnas=columnas,
            filas=filas,
            torneos=torneos_,
            torneo=t,
            fecha=f,
            n=n,
        )

