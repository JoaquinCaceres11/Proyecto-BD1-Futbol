from datetime import date, datetime
from flask import flash, redirect, request, url_for
from db import consulta, ejecutar
from helpers import CAMPOS_JUGADOR, CI_RE, EMAIL_RE, TIPOS, accion, admin, campo, cuenta, fila, formulario, form_get, opciones, pagina, tabla, validar


def validar_jugador(f, creando=True):
    nac_ok = False
    try:
        nac = datetime.strptime(f["fecha_nacimiento"], "%Y-%m-%d").date()
        nac_ok = nac < date.today() and (date.today() - nac).days >= 16 * 365
    except ValueError:
        pass

    return validar([
        (not creando or CI_RE.match(f["ci"]), "CI invalida (7 u 8 digitos)."),
        (f["nombre"] and len(f["nombre"]) <= 50, "Nombre requerido (max 50)."),
        (f["apellido"] and len(f["apellido"]) <= 50, "Apellido requerido (max 50)."),
        (EMAIL_RE.match(f["email"]) and len(f["email"]) <= 100, "Email invalido."),
        (nac_ok, "Fecha de nacimiento invalida (minimo 16 anios)."),
        (f["tipo"] in TIPOS, "Tipo invalido."),
        (f["id_facultad"].isdigit(), "Selecciona una facultad."),
    ])


def campos_jugador(v=None, creando=True):
    v = v or {}
    fac = opciones("SELECT id_facultad AS valor, nombre AS texto FROM facultad ORDER BY nombre")
    return [
        campo("ci", "CI", extra='required pattern="[0-9]{7,8}" maxlength="8"' + ("" if creando else " readonly"), valor=v.get("ci", "")),
        campo("nombre", "Nombre", extra='required maxlength="50"', valor=v.get("nombre", "")),
        campo("apellido", "Apellido", extra='required maxlength="50"', valor=v.get("apellido", "")),
        campo("email", "Email", "email", extra='required maxlength="100"', valor=v.get("email", "")),
        campo("fecha_nacimiento", "Fecha de nacimiento", "date", extra="required", valor=str(v.get("fecha_nacimiento", ""))),
        campo("id_facultad", "Facultad", "select", fac, v.get("id_facultad", "")),
        campo("tipo", "Tipo", "select", [(t, t) for t in TIPOS], v.get("tipo", "")),
    ]


def register_jugadores_routes(app):
    @app.route("/jugadores", methods=["GET", "POST"])
    @admin
    def jugadores():
        if request.method == "POST":
            f = dict(zip(CAMPOS_JUGADOR, form_get(*CAMPOS_JUGADOR)))
            if validar_jugador(f):
                ejecutar("INSERT INTO jugador (ci, nombre, apellido, email, fecha_nacimiento, id_facultad, tipo) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                         (f["ci"], f["nombre"], f["apellido"], f["email"], f["fecha_nacimiento"], int(f["id_facultad"]), f["tipo"]), "Jugador creado.")
            return redirect(url_for("jugadores"))

        filas = consulta("SELECT j.ci, j.nombre, j.apellido, j.email, j.tipo, f.nombre AS facultad FROM jugador j JOIN facultad f ON f.id_facultad = j.id_facultad ORDER BY j.apellido, j.nombre")
        for r in filas:
            r["_acciones"] = [accion("Editar", url_for("jugador_editar", ci=r["ci"]), "get"),
                              accion("Eliminar", url_for("jugador_eliminar", ci=r["ci"]), confirmar=True)]
        form = formulario("Nuevo jugador", url_for("jugadores"), campos_jugador(), "Crear jugador")
        return pagina("Jugadores", [form], [tabla("Listado de jugadores", ["ci", "nombre", "apellido", "email", "tipo", "facultad"], filas, True)])

    @app.route("/jugadores/<ci>/editar", methods=["GET", "POST"])
    @admin
    def jugador_editar(ci):
        if not CI_RE.match(ci):
            flash("CI invalida.", "error")
            return redirect(url_for("jugadores"))

        actual = fila("SELECT * FROM jugador WHERE ci = %s", (ci,))
        if not actual:
            flash("El jugador no existe.", "error")
            return redirect(url_for("jugadores"))

        if request.method == "POST":
            f = dict(zip(CAMPOS_JUGADOR, form_get(*CAMPOS_JUGADOR)))
            f["ci"] = ci

            # Validar facultad si esta en torneo activo
            cambia_fac = str(f["id_facultad"]) != str(actual["id_facultad"])
            activo = cuenta("SELECT COUNT(*) FROM equipo_jugador_torneo ejt JOIN torneo t ON t.id_torneo = ejt.id_torneo WHERE ejt.ci_jugador = %s AND t.estado <> 'finalizado'", (ci,)) > 0
            # Validar cupo de docentes/funcionarios
            nuevo_staff = f["tipo"] in ("docente", "funcionario") and actual["tipo"] not in ("docente", "funcionario")
            cupo_lleno = cuenta("SELECT COUNT(*) FROM equipo_jugador_torneo propio JOIN torneo t ON t.id_torneo = propio.id_torneo "
                                "JOIN equipo_jugador_torneo otro ON otro.id_equipo = propio.id_equipo AND otro.ci_jugador <> propio.ci_jugador "
                                "JOIN jugador j ON j.ci = otro.ci_jugador WHERE propio.ci_jugador = %s AND t.estado <> 'finalizado' AND j.tipo IN ('docente','funcionario')", (ci,)) >= 2

            if cambia_fac and activo:
                flash("El jugador integra un plantel en un torneo activo: no puede cambiar de facultad.", "error")
            elif nuevo_staff and cupo_lleno:
                flash("El plantel del jugador ya tiene 2 docentes/funcionarios.", "error")
            elif validar_jugador(f, creando=False):
                ejecutar("UPDATE jugador SET nombre=%s, apellido=%s, email=%s, fecha_nacimiento=%s, id_facultad=%s, tipo=%s WHERE ci=%s",
                         (f["nombre"], f["apellido"], f["email"], f["fecha_nacimiento"], int(f["id_facultad"]), f["tipo"], ci), "Jugador modificado.")
                return redirect(url_for("jugadores"))
            return redirect(url_for("jugador_editar", ci=ci))

        form = formulario("Datos del jugador", url_for("jugador_editar", ci=ci), campos_jugador(actual, creando=False), "Guardar cambios")
        return pagina(f"Editar jugador {ci}", [form])

    @app.route("/jugadores/<ci>/eliminar", methods=["POST"])
    @admin
    def jugador_eliminar(ci):
        if not CI_RE.match(ci):
            flash("CI invalida.", "error")
        elif cuenta("SELECT COUNT(*) FROM equipo_jugador_torneo WHERE ci_jugador = %s", (ci,)) > 0:
            flash("No se puede eliminar: el jugador integra un plantel. Quitalo del plantel primero.", "error")
        else:
            ejecutar("DELETE FROM jugador WHERE ci = %s", (ci,), "Jugador eliminado.")
        return redirect(url_for("jugadores"))
