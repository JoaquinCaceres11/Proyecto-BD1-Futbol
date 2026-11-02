from routes.auth import register_auth_routes
from routes.torneos import register_torneos_routes
from routes.jugadores import register_jugadores_routes
from routes.equipos import register_equipos_routes
from routes.complejos import register_complejos_routes
from routes.partidos import register_partidos_routes
from routes.sanciones import register_sanciones_routes
from routes.reportes import register_reportes_routes


def register_all_routes(app):
    register_auth_routes(app)
    register_torneos_routes(app)
    register_jugadores_routes(app)
    register_equipos_routes(app)
    register_complejos_routes(app)
    register_partidos_routes(app)
    register_sanciones_routes(app)
    register_reportes_routes(app)

