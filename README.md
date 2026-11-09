# Torneo Interfacultades de Fútbol 5 – UCU (Base de Datos 1, 2026)

Sistema web para gestionar el Torneo Interfacultades de Fútbol 5: jugadores, equipos y planteles, complejos y
canchas, fixture, planillas de juego (goles y tarjetas), sanciones y reportes.

**Integrantes:** Joaquín Bauza y Joaquín Cáceres

- **Backend:** Python 3 + Flask, con SQL escrito a mano mediante `mysql-connector-python` (**sin ORM**).
- **Base de datos:** MySQL 8.
- **Frontend:** plantillas HTML (Jinja) servidas por Flask.
- **Despliegue:** Docker y Docker Compose.

El informe con las decisiones de diseño está en [`informe.md`](informe.md).

## Estructura

```
sql/01_schema.sql     tablas, restricciones, vista y usuarios de base de datos con permisos
sql/02_datos.sql      datos maestros y datos de prueba (6 equipos, 3 fechas jugadas)
sql/03_reportes.sql   las 12 consultas de reportes (9 pedidas + 3 propias); la app las lee de este archivo
app/app.py            punto de entrada de la aplicación Flask
app/db.py             conexión a MySQL según el rol, consultas y transacciones
app/helpers.py        validaciones, decoradores de permisos y utilidades de las pantallas
app/routes/           una ruta por módulo: jugadores, equipos, complejos, torneos, partidos, sanciones, reportes
app/templates/        plantillas HTML
Dockerfile, docker-compose.yml
```

## Opción A – Con Docker (recomendada)

Requisito: Docker Desktop abierto.

```bash
docker compose up --build
```

La primera vez, MySQL ejecuta `01_schema.sql` y `02_datos.sql`. Cuando termine de levantar, abrir
<http://localhost:5000>.

- Para detener: `Ctrl+C` o `docker compose down`. **Los datos se conservan.**
- Para reiniciar la base desde cero (**borra los datos cargados a mano**):

  ```bash
  docker compose down -v
  docker compose up --build
  ```

MySQL corre con la hora de Uruguay (`--default-time-zone=-03:00`), necesaria para las reglas que dependen
del día y turno de los partidos.

## Opción B – Sin Docker

Requisitos: Python 3.10+ y MySQL 8 corriendo en local, configurado con la hora local.

1. Crear la base y cargar los datos con un usuario administrador (por ejemplo `root`):

   ```bash
   mysql -u root -p < sql/01_schema.sql
   mysql -u root -p < sql/02_datos.sql
   ```

2. Instalar las dependencias y correr la aplicación:

   ```bash
   cd app
   python -m venv venv
   venv\Scripts\activate           # en Linux/Mac: source venv/bin/activate
   pip install -r requirements.txt
   python app.py
   ```

   Por defecto se conecta a `localhost:3306`. Si MySQL está en otro host o puerto, definir las variables
   `DB_HOST` y `DB_PORT` antes de correr la app.

3. Abrir <http://localhost:5000>.

## Usuarios de la aplicación

| Rol | Correo | Contraseña | Qué puede hacer |
|---|---|---|---|
| administrador | admin@ucu.edu.uy | `admin123` | Todo: ABM, partidos, planillas, sanciones y reportes |
| planillero | planillero@ucu.edu.uy | `planillero123` | Ver el fixture, cargar planillas, goles y tarjetas, y marcar partidos como jugados |

Además hay dos usuarios de **base de datos** con permisos distintos (`app_admin` y `app_planillero`). La
aplicación se conecta con uno u otro según el rol de quien inició sesión (ver `sql/01_schema.sql`).

## Qué probar

- **Reportes** (administrador → *Reportes*). Con los datos de prueba:
  - Tabla de posiciones: 1° Los Contadores (7 pts, DG +4), 2° Mente Sana (7 pts, DG +2),
    3° Ingenieros FC (6 pts), 4° Salud Total (4 pts), 5° Letras y Goles (1 pt), 6° Abogados United (0 pts).
  - Promedio de goles de la edición: 2.89 (26 goles en 9 partidos).
- **Regla de las 48 horas:** la planilla del partido 1 ya no se puede modificar. El partido 10 tiene fecha de
  ayer: se puede cargar su planilla, marcarlo como jugado y corregirlo durante 48 horas.
- **Partidos no disputados:** programar un partido a futuro y abrir su planilla; no permite cargar datos.
- **Suspensiones:** en la planilla del partido 10, Pérez, Martín (3 amarillas) no se puede agregar.
- **Sanciones automáticas:** registrar una roja en el partido 10 genera la sanción para la fecha siguiente;
  al eliminar la tarjeta, la sanción se revierte.
- **Reglas del plantel:** agregar un 11° jugador, un 3° docente o funcionario, o un jugador de otra facultad.
- **Reglas del fixture:** repetir un cruce, un equipo dos veces en la misma fecha, o dos partidos en la misma
  cancha, día y turno.
- **Permisos:** entrar como planillero y verificar que no accede a los ABM ni a los reportes.
