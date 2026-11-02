# Torneo Interfacultades de Fútbol 5 – UCU (Base de Datos 1, 2026)

Sistema para gestionar el torneo: equipos y planteles, fixture, planillas de juego (goles y tarjetas),
sanciones y reportes. **Entrega: avance (30/10/2026).**

- Backend: Python 3 + Flask, SQL escrito a mano con `mysql-connector-python` (**sin ORM**).
- Base de datos: MySQL 8.
- Frontend: plantillas HTML (Jinja) servidas por Flask.

## Estructura

```
sql/01_schema.sql     tablas, restricciones, triggers, vista y usuarios de BD
sql/02_datos.sql      datos maestros + datos de prueba (6 equipos, 3 fechas jugadas)
sql/03_reportes.sql   las 12 consultas de reportes (9 pedidas + 3 propias)
app/                  aplicación Flask (app.py + templates/)
Dockerfile, docker-compose.yml
```

## Opción A – Con Docker (recomendada)

Requisito: Docker Desktop.

```bash
docker compose up --build
```

La primera vez, MySQL ejecuta solo `01_schema.sql` y `02_datos.sql`. Cuando termine de levantar:
abrir <http://localhost:5000>.

Para reiniciar la base desde cero (borra los datos):

```bash
docker compose down -v
docker compose up --build
```

## Opción B – Sin Docker

Requisitos: Python 3.10+, MySQL 8 corriendo en local.

1. Crear la base y cargar los datos (con un usuario con permisos de administración, p. ej. `root`):

   ```bash
   mysql -u root -p < sql/01_schema.sql
   mysql -u root -p < sql/02_datos.sql
   ```

2. Instalar dependencias y correr la app:

   ```bash
   cd app
   python -m venv venv
   source venv/bin/activate        # en Windows: venv\Scripts\activate
   pip install -r requirements.txt
   python app.py
   ```

   Por defecto se conecta a `localhost:3306`. Si MySQL está en otro host/puerto, definir las variables
   `DB_HOST` y `DB_PORT` antes de correr (por ejemplo `DB_HOST=127.0.0.1 DB_PORT=3307 python app.py`).

3. Abrir <http://localhost:5000>.

## Usuarios de la aplicación

| Rol           | Correo                  | Contraseña       | Qué puede hacer                                   |
|---------------|-------------------------|------------------|---------------------------------------------------|
| administrador | admin@ucu.edu.uy        | `admin123`       | Todo: ABMs, partidos, planillas, sanciones, reportes |
| planillero    | planillero@ucu.edu.uy   | `planillero123`  | Ver el fixture, marcar jugado y cargar planilla/goles/tarjetas |

Además hay dos usuarios de **base de datos** con permisos distintos (`app_admin` y `app_planillero`);
la aplicación se conecta con uno u otro según el rol de quien inició sesión (ver `01_schema.sql`).

## Qué probar

- **Reportes** (como administrador → *Reportes*). Resultados esperados con los datos de prueba:
  - Tabla de posiciones: 1° Los Contadores (7 pts, DG +4), 2° Mente Sana (7 pts, DG +2),
    3° Ingenieros FC (6 pts), 4° Salud Total (4 pts), 5° Letras y Goles (1 pt), 6° Abogados United (0 pts).
  - Promedio de goles de toda la edición: 2.89 (26 goles en 9 partidos).
- **Reglas del plantel**: intentar agregar un 11° jugador, un 3° docente/funcionario, o un jugador de otra facultad.
- **Reglas del fixture**: programar el mismo cruce dos veces, un equipo dos veces en la misma fecha,
  o dos partidos en la misma cancha, día y turno.
- **Suspensiones**: Salud Total (jugador con roja en la fecha 1) no puede figurar en la planilla de la fecha 2;
  el trigger de la base lo rechaza.
- **Permisos**: entrar como planillero y verificar que no ve el menú de ABMs ni los reportes.

## Notas del avance

Está implementado lo central de cada requerimiento. Lo que queda para la entrega final está listado
en la sección "Pendientes" del informe.
