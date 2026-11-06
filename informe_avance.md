# Informe de avance – Sistema para la Gestión del Torneo Interfacultades de Fútbol 5

**Materia:** Base de Datos 1 – Universidad Católica del Uruguay – Segundo semestre 2026
**Integrantes:** [COMPLETAR]
**Fecha de avance:** 30/10/2026

---

## 1. Alcance del avance

Este avance entrega la base de datos completa (esquema, restricciones, triggers, usuarios y datos de prueba),
los 12 reportes en SQL y una primera versión funcional de la aplicación con los ABM principales,
el registro de planillas y el sistema de reportes.

| Requerimiento | Estado |
|---|---|
| Script SQL de creación + datos maestros + datos de prueba (6 equipos, 3 fechas) | Hecho |
| ABM de jugadores | Hecho |
| ABM de equipos y planteles (con capitán) | Hecho |
| ABM de complejos y canchas | Hecho |
| ABM de partidos con reglas de programación | Hecho |
| Planillas, goles y tarjetas | Hecho |
| Sanciones automáticas (roja / 3 amarillas) y ABM de sanciones disciplinarias | Hecho |
| 9 reportes pedidos + 3 consultas propias | Hecho |
| Usuarios de BD con permisos diferenciados | Hecho |
| Docker y docker-compose | Hecho |
| Validación en front-end, back-end y base de datos | Hecho (básica, ver sección 5) |

## 2. Modelo de datos

Se respetaron las 14 tablas de la letra. Decisiones y agregados:

**Atributos agregados**

- `partido.fecha_jugado` (DATETIME): momento en que el partido se marcó como jugado. Se necesita para
  la regla de las 48 horas para corregir un resultado.

**Restricciones adicionales (mejoras al modelo)**

- `UNIQUE (anio, semestre)` en `torneo`: hay una única edición por semestre.
- `UNIQUE (id_torneo, id_facultad)` en `equipo`: una facultad representa a un solo equipo por edición.
- `UNIQUE (ci_jugador, id_torneo)` en `equipo_jugador_torneo`: un jugador no puede estar en dos equipos
  de la misma edición.
- `UNIQUE (id_equipo, numero_camiseta)`: no se repite el número de camiseta dentro de un plantel.
- `CHECK` de formato de CI, email, rango de minutos (1–60), turnos entre 18:00 y 23:00, semestre 1 o 2,
  cantidad de fechas de sanción mayor o igual a 1, y equipo local distinto del visitante.
- `gol` y `tarjeta` tienen clave foránea compuesta hacia `planilla_partido (id_partido, ci_jugador)`:
  así la base garantiza que solo pueden convertir goles o recibir tarjetas jugadores que figuran en la planilla.
- `equipo.ci_capitan` admite `NULL` al crear el equipo (el plantel todavía está vacío) y un trigger exige
  que luego sea un jugador del propio plantel.

**Vista**

- `v_resultado_partido`: calcula el resultado de cada partido jugado a partir de los goles registrados
  (un autogol suma al rival). Es la base de la tabla de posiciones y de otros reportes; el resultado nunca se
  guarda como dato, así no puede quedar inconsistente con los goles.

**Valores de los ENUM**: se escribieron sin tildes (`sintetico`, `inscripcion`) para evitar problemas de codificación.

## 3. Reglas de negocio y en qué capa se controlan

Siguiendo las pautas de diseño y evitando el uso de triggers en el motor relacional, las reglas de negocio se dividen de forma limpia entre **restricciones declarativas de base de datos** (`CHECK`, `UNIQUE`, `FOREIGN KEY`, `NOT NULL`) y la **capa de backend (Python / Flask)**:

| Regla | Base de datos (Declarativa) | Back-end (Lógica de negocio) |
|---|---|---|
| Plantel de 5 a 10 jugadores | — | Chequeo de cupo (máximo 10) al agregar; mínimo 5 al pasar a "en curso" y al programar partidos |
| Máx. 2 docentes/funcionarios por plantel | — | Validación en backend al agregar al plantel o editar jugador |
| Jugador de la misma facultad que el equipo | — | Filtro en interfaz y validación estricta de pertenencia en backend |
| Un jugador, un equipo por edición | `UNIQUE (ci_jugador, id_torneo)` | Validación previa y listado exclusivo de jugadores disponibles |
| Plantel modificable solo en inscripción | — | Validación de estado del torneo en rutas de agregar/quitar jugador |
| Capitán es jugador del plantel | — | Validación de pertenencia al plantel antes de actualizar capitán; impedimento de quitarlo del plantel |
| Equipos de la misma edición con al menos 5 jugadores | `CHECK` / FKs | Verificación de pertenencia y cantidad mínima de jugadores antes de programar |
| No jugar contra sí mismo ni repetir rival (salvo cancelado) | `CHECK (id_equipo_local <> id_equipo_visitante)` | Validación previa en creación de partido y algoritmo de fixture |
| Un partido por equipo por fecha | — | Consulta de verificación antes de insertar o reprogramar partidos |
| Una cancha por día y turno | — | Consulta de disponibilidad de cancha/turno antes de programar o reprogramar |
| Solo jugadores del plantel y no suspendidos en la planilla | FK compuesta en tablas relacionadas | Validación de pertenencia al plantel y consulta de suspensiones activas para la fecha |
| Goles y tarjetas solo de jugadores de la planilla | FK compuesta hacia `planilla_partido(id_partido, ci_jugador)` | Validación y opciones restringidas a jugadores en planilla |
| Marcar jugado solo si el día y turno ya pasaron | — | Validación contra `NOW()` y existencia de planilla de ambos equipos |
| Partido jugado no se elimina | — | Validación en ruta de eliminación de partido |
| Corrección del resultado dentro de las 48 hs | — | Control en backend (`TIMESTAMPDIFF(HOUR, fecha_jugado, NOW()) < 48`) en edición de planillas, goles y tarjetas |
| Sanción automática por roja y por acumulación de amarillas | — | Lógica automática en backend tras registrar tarjeta: genera sanción para la fecha siguiente y revierte si se borra |
| Fixture liga a una sola rueda | — | Algoritmo Round-Robin automatizado en el panel de torneos |

## 4. Seguridad a nivel de base de datos

Se crean dos usuarios de MySQL con privilegios diferenciados:

- `app_admin`: `SELECT, INSERT, UPDATE, DELETE` sobre toda la base.
- `app_planillero`: `SELECT` solo sobre las tablas del torneo (**no** sobre `login`), escritura (`SELECT, INSERT, UPDATE, DELETE`) únicamente sobre `planilla_partido`, `gol`, `tarjeta` y `sancion_jugador` (para registro automático de sanciones derivadas del partido), y `UPDATE` limitado a las columnas `estado` y `fecha_jugado` de `partido`.

La aplicación abre la conexión con el usuario que corresponde al rol del usuario logueado, de modo que aunque
hubiera un error en la aplicación, la base impide que un planillero modifique datos que no le corresponden.

Las contraseñas de la aplicación se guardan con hash SHA-256 (`SHA2()` de MySQL) y las consultas usan
parámetros (`%s`) para evitar inyección SQL. Además, todos los formularios cuentan con protección contra ataques CSRF.

## 5. Validación en tres capas

1. **Front-end:** atributos HTML (`required`, `pattern`, `min`, `max`, `maxlength`, tipos `email`, `date`, `number`).
2. **Back-end:** funciones de validación en Python antes de ejecutar cada consulta (formato de CI y email,
   edad mínima, rangos de minutos y fechas, estados válidos del torneo, disponibilidad de turnos/canchas, suspensiones vigentes, etc.).
3. **Base de datos:** Restricciones declarativas: `CHECK`, `UNIQUE`, claves foráneas compuestas, `ENUM`, `NOT NULL`. Los errores de integridad son capturados amigablemente.

## 6. Reportes

Los reportes están en `sql/03_reportes.sql` y la aplicación los lee de ese mismo archivo (una sola fuente).
R1 a R9 son los pedidos. Las tres consultas propias son:

- **R10 – Jugadores en riesgo:** jugadores con 2 amarillas (la tercera los suspende). Ayuda a los equipos
  y a la organización a anticipar suspensiones.
- **R11 – Jugadores suspendidos en una fecha dada:** sirve al planillero y a la organización para saber
  quién no puede figurar en la planilla de la próxima fecha.
- **R12 – Partidos con más goles:** métrica de espectáculo para el área de deportes.

## 7. Datos de prueba

6 equipos de 7 jugadores cada uno (42 jugadores, con docentes, posgrado y funcionarios), 2 complejos, 4 canchas,
5 turnos, 9 partidos jugados (fechas 1 a 3), 1 partido programado, 1 postergado y 1 cancelado (fecha 4).
Incluyen un autogol, rojas, acumulación de amarillas y una sanción disciplinaria, para que todos los reportes
devuelvan datos. Los jugadores inscriptos que nunca figuran en una planilla (para el reporte R7) son el séptimo
jugador de cada plantel y el sexto de varios equipos.

## 8. Mejoras implementadas y consideraciones para la entrega final

- **Arquitectura en capas sin triggers:** Toda la lógica de negocio, validaciones complejas y automatizaciones se concentraron en la capa de backend en Python, manteniendo el esquema de base de datos puramente relacional y declarativo (`CHECK`, `UNIQUE`, `FOREIGN KEY`).
- **Control de edición en 48 horas:** Se valida en backend que tras 48 horas de disputado un partido (`NOW() - fecha_jugado >= 48 hs`), las planillas, goles y tarjetas queden congeladas para edición.
- **Fixture automático Round-Robin:** Se incorporó en la aplicación el generador de liga a una sola rueda que programa automáticamente todas las fechas y partidos rotando turnos y canchas sin solapamiento.
- **Reprogramación de partidos postergados:** Se implementó la ruta y formulario de reprogramación para reasignar día, turno, cancha y fecha a los partidos suspendidos/postergados, verificando disponibilidad de cancha y fixture.
- **Protección web contra ataques CSRF:** Se incorporaron tokens de protección CSRF en todos los formularios del sistema y se fortaleció la clave secreta de sesión.
- **Automatización de sanciones por tarjetas:** El backend aplica automáticamente la suspensión para la fecha siguiente ante tarjeta roja o acumulación de tarjetas amarillas (cada 3 amarillas: 3, 6, 9...), revirtiéndolas si se cancela o elimina la tarjeta.
- **Consultas con Funciones de Ventana:** El reporte R12 implementa `DENSE_RANK() OVER (ORDER BY total_goles DESC)` para generar un ranking analítico de los partidos con más goles de la edición.

**Trabajo futuro / Oportunidades de mejora:**
- Pasar el almacenamiento de contraseñas a un hash con sal y coste adaptable (como bcrypt o Argon2) en lugar de SHA-256 simple.
- Gestión de postergaciones con reprogramación flexible de sanciones (en caso de fechas postergadas de forma asincrónica).

## 9. Bitácora del trabajo realizado

| Fecha | Actividad | Responsable |
|---|---|---|
| 09/10/2026 | Entrega de la letra. Lectura y análisis de requerimientos | [COMPLETAR] |
| [COMPLETAR] | Diseño del modelo relacional y decisiones de restricciones | [COMPLETAR] |
| 30/10/2026 | Script de creación, triggers y usuarios de BD. Datos de prueba. Reportes SQL | [COMPLETAR] |
| 30/10/2026 | Backend Flask: login, ABMs, planillas y reportes. Docker y documentación del avance | [COMPLETAR] |

*Se utilizó un asistente de inteligencia artificial (Claude, de Anthropic) como apoyo en la preparación de este
avance; el equipo revisó y es responsable del contenido entregado. [Ajustar o eliminar según la política de la cátedra.]*

## 10. Bibliografía

- Oracle. *MySQL 8.0 Reference Manual* (CREATE TRIGGER, CHECK constraints, GRANT, Window/CTE, WITH ROLLUP). <https://dev.mysql.com/doc/refman/8.0/en/>
- Pallets Projects. *Flask Documentation*. <https://flask.palletsprojects.com/>
- Oracle. *MySQL Connector/Python Developer Guide*. <https://dev.mysql.com/doc/connector-python/en/>
- Docker Inc. *Docker Compose documentation*. <https://docs.docker.com/compose/>
- Material teórico y prácticos del curso de Base de Datos 1, UCU (2026).
