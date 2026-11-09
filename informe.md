# Informe final – Sistema para la Gestión del Torneo Interfacultades de Fútbol 5

**Materia:** Base de Datos 1 – Universidad Católica del Uruguay – Segundo semestre 2026
**Integrantes:** Joaquín Bauza y Joaquín Cáceres
**Repositorio:** <https://github.com/JoaquinCaceres11/Proyecto-BD1-Futbol>

---

## 1. Resumen

El sistema permite gestionar una edición completa del torneo: jugadores, equipos y planteles, complejos y
canchas, programación de partidos, planillas de juego con goles y tarjetas, sanciones y reportes. Está
construido con Python y Flask, una base MySQL 8 con SQL escrito a mano (sin ORM) y se levanta con Docker
Compose. Las instrucciones para ejecutarlo están en el `README.md`.

| Requerimiento | Estado |
|---|---|
| Script de creación, datos maestros y datos de prueba | Hecho |
| ABM de jugadores | Hecho |
| ABM de equipos y planteles (con capitán y número de camiseta) | Hecho |
| ABM de complejos y canchas | Hecho |
| ABM de partidos con reglas de programación y reprogramación | Hecho |
| Registro de planillas, goles y tarjetas | Hecho |
| Sanciones automáticas y ABM de sanciones disciplinarias | Hecho |
| 9 reportes pedidos y 3 consultas propias | Hecho |
| Usuarios de base de datos con permisos diferenciados | Hecho |
| Validación en front-end, back-end y base de datos | Hecho |
| Docker y Docker Compose | Hecho |

## 2. Decisiones de implementación

**Flask con SQL escrito a mano.** La letra no permite ORM. Escribir las consultas a mano nos dio control
sobre cada `JOIN` y cada restricción, y nos obligó a pensar el modelo en términos relacionales. Todas las
consultas usan parámetros (`%s`) para evitar inyección SQL.

**Reglas de negocio en el backend, sin triggers.** Investigamos los triggers y llegamos a implementar
varios, pero decidimos no usarlos. Concentramos las reglas complejas (cupos del plantel, suspensiones,
fixture, regla de las 48 horas, sanciones automáticas) en el backend de Python, y dejamos en la base las
restricciones declarativas (`CHECK`, `UNIQUE`, `FOREIGN KEY`, `ENUM`, `NOT NULL`). Así la lógica queda en
un solo lugar, es más fácil de leer, de depurar y de mostrar al usuario con mensajes claros. La contrapartida
es que un acceso SQL directo a la base podría saltear esas reglas. Lo mitigamos con usuarios de base de datos
con permisos mínimos y con el hecho de que la aplicación es el único punto de acceso previsto.

**Dos usuarios de base de datos.** La aplicación se conecta como `app_admin` o como `app_planillero` según
el rol de quien inició sesión. De esta forma, aunque hubiera un error en la aplicación, la propia base impide
que un planillero modifique datos que no le corresponden (ver sección 4).

**Transacciones en tarjetas y sanciones.** Una tarjeta roja o la tercera amarilla generan una sanción
automática. La tarjeta y su sanción se guardan en una única transacción (`commit` / `rollback`): se guardan
las dos o ninguna, así nunca queda una tarjeta sin su sanción. Lo mismo ocurre al eliminar una tarjeta, que
revierte la sanción correspondiente.

**El resultado no se guarda, se calcula.** La vista `v_resultado_partido` calcula el resultado a partir de
los goles registrados (un autogol suma al rival). Al no duplicar el dato, el resultado nunca puede quedar
inconsistente con los goles.

**Regla de las 48 horas desde la disputa.** El plazo para corregir un resultado se cuenta desde el fin del
turno en que se jugó el partido (`TIMESTAMP(dia, hora_fin)`), no desde el momento en que alguien lo marcó
como jugado. También se impide cargar planilla en un partido que todavía no se disputó, o que está postergado
o cancelado.

**Estados del partido.** Un partido jugado no se elimina ni cambia de estado. No se puede cancelar ni
postergar un partido que ya tiene planilla. Un partido postergado debe reprogramarse (con otro día o turno,
dentro de las fechas del torneo) antes de poder jugarse.

**Plantillas HTML en lugar de React.** Evaluamos hacer el frontend en React, pero priorizamos la base de
datos y las reglas de negocio, que son el foco de la materia. Las plantillas Jinja servidas por Flask nos
permitieron tener toda la aplicación funcionando con menos piezas.

**Docker Compose.** Cualquier persona levanta la base y la aplicación con un solo comando, sin instalar
MySQL ni Python. MySQL se configura con la hora de Uruguay, necesaria para las reglas que dependen de
`NOW()`.

## 3. Modelo de datos

Se respetaron las 14 tablas de la letra, con estos agregados y restricciones:

**Atributo agregado**

- `partido.fecha_jugado` (DATETIME): momento en que el partido se marcó como jugado.

**Restricciones adicionales (mejoras al modelo)**

- `UNIQUE (anio, semestre)` en `torneo`: una única edición por semestre.
- `UNIQUE (id_torneo, nombre)` y `UNIQUE (id_torneo, id_facultad)` en `equipo`: en una edición, cada
  facultad presenta un solo equipo y no se repiten nombres.
- `UNIQUE (ci_jugador, id_torneo)` en `equipo_jugador_torneo`: un jugador no puede estar en dos equipos de
  la misma edición.
- `UNIQUE (id_equipo, numero_camiseta)` y `CHECK` de camiseta entre 1 y 99.
- `CHECK` de formato de CI y email, minutos entre 1 y 60, turnos válidos, semestre 1 o 2, fechas del torneo
  coherentes, sanciones de al menos una fecha y equipo local distinto del visitante.
- `gol` y `tarjeta` tienen clave foránea compuesta hacia `planilla_partido (id_partido, ci_jugador)`: la base
  garantiza que solo convierten goles o reciben tarjetas jugadores que figuran en la planilla.
- `equipo.ci_capitan` admite `NULL` al crear el equipo, porque el plantel todavía está vacío. El backend
  exige que el capitán sea del plantel y que todos los equipos tengan capitán y al menos 5 jugadores.

**Valores de los ENUM:** se escribieron sin tildes (`sintetico`, `inscripcion`) para evitar problemas de
codificación.

## 4. Seguridad

- `app_admin`: `SELECT, INSERT, UPDATE, DELETE` sobre toda la base.
- `app_planillero`: `SELECT` sobre las tablas del torneo (**no** sobre `login`); escritura sobre
  `planilla_partido`, `gol` y `tarjeta`; `UPDATE` limitado a las columnas `estado` y `fecha_jugado` de
  `partido`; e `INSERT`/`DELETE` sobre `sancion_jugador`. Este último permiso existe porque la sanción
  automática se guarda en la misma transacción que la tarjeta: el planillero no carga sanciones a mano, la
  aplicación las genera junto con la tarjeta.
- Contraseñas de la aplicación guardadas con hash SHA-256.
- Consultas parametrizadas y protección CSRF en todos los formularios.
- Control de rol en cada ruta del backend: no alcanza con esconder botones en la interfaz.

## 5. Validación en tres capas

1. **Front-end:** atributos HTML (`required`, `min`, `max`, `maxlength`, tipos `email`, `date`, `number`).
2. **Back-end:** validaciones en Python antes de cada operación: formatos, rangos, estados del torneo y del
   partido, cupos del plantel, disponibilidad de cancha y turno, suspensiones vigentes y regla de las 48 horas.
3. **Base de datos:** `CHECK`, `UNIQUE`, claves foráneas (incluidas las compuestas), `ENUM` y `NOT NULL`.

## 6. Reportes

Los reportes están en `sql/03_reportes.sql`, y la aplicación los lee de ese archivo. R1 a R9 son los pedidos.
Los reportes de goles, tarjetas y fair play consideran solo partidos jugados. Las tres consultas propias son:

- **R10 – Jugadores en riesgo de suspensión:** jugadores con 2 amarillas; la tercera los suspende. Ayuda a
  anticipar suspensiones.
- **R11 – Jugadores suspendidos en una fecha:** útil para saber quién no puede figurar en la planilla de la
  próxima fecha.
- **R12 – Partidos con más goles:** ranking con la función de ventana `DENSE_RANK()`.

## 7. Datos de prueba

6 equipos de 7 jugadores (42 jugadores, con estudiantes de grado y posgrado, docentes y funcionarios),
2 complejos, 4 canchas y 5 turnos. Hay 9 partidos jugados (fechas 1 a 3) y, en la fecha 4, uno programado,
uno postergado y uno cancelado. Incluyen un autogol, tarjetas rojas, acumulación de amarillas, una sanción
disciplinaria y jugadores que nunca figuraron en una planilla, para que todos los reportes devuelvan datos.
El partido programado tiene fecha del día anterior a la carga, para poder mostrar la regla de las 48 horas.

## 8. Limitaciones conocidas y mejoras futuras

- **Sin triggers:** las reglas de negocio viven en el backend. Como mejora, podrían agregarse triggers como
  respaldo para cubrir accesos SQL directos.
- **Fixture automático:** el generador de liga a una rueda no valida que todas las fechas entren en el período
  del torneo ni la disponibilidad de canchas usadas por otros torneos.
- **Contraseñas:** se usa SHA-256 sin sal; lo recomendable es un hash con sal y coste adaptable (bcrypt,
  Argon2 o `werkzeug.security`).
- **Mensajes de error:** algunos errores de integridad de MySQL (por ejemplo, eliminar un complejo con
  canchas) se muestran con el texto original del motor.
- **Casos no pedidos por la letra:** un equipo podría jugar dos partidos el mismo día y turno en canchas
  distintas, y un torneo se puede finalizar con partidos pendientes.

## 9. Bitácora

1. **Análisis de la letra:** lectura de los requerimientos, identificación de las entidades, las reglas de
   negocio y los reportes pedidos.
2. **Modelo de datos:** diseño del modelo relacional y creación de las tablas, con sus claves, restricciones
   `CHECK`, `UNIQUE` y claves foráneas, la vista de resultados y los usuarios de base de datos.
3. **Entrega de avance:** carga de datos de prueba, escritura de los reportes en SQL y primera versión de la
   aplicación con login, ABM principales y planillas.
4. **Correcciones iniciales:** arreglo de la pantalla de sanciones y de la carga de los reportes en la aplicación.
5. **Pruebas con triggers:** implementación de triggers para controlar la reprogramación de partidos y revertir
   sanciones. Luego se descartaron.
6. **Reglas en el backend:** migración de las reglas de negocio a Python, sin triggers, y revisión de casos borde.
7. **Reglas de partidos:** regla de las 48 horas contada desde la disputa, bloqueo de planillas en partidos no
   disputados y sanciones coherentes en los datos de prueba.
8. **Completar los ABM:** modificación de partidos, equipos, camisetas, complejos, canchas y sanciones
   disciplinarias.
9. **Ajustes de reportes:** los reportes de goles, tarjetas y fair play pasan a considerar solo partidos jugados,
   y no se permite cancelar partidos con planilla cargada.
10. **Integridad de datos:** transacción para guardar juntas la tarjeta y su sanción automática.
11. **Cierre:** limpieza del repositorio, prueba completa desde cero, informe y README.

## 10. Experiencia del equipo

**Joaquín Bauza.** Para el proyecto me informé sobre cómo funcionan los triggers. Llegamos a implementar
varios, para controlar la reprogramación de partidos y para revertir sanciones al eliminar una tarjeta, y
después decidimos no usarlos y llevar esas reglas al backend. Esa discusión fue de lo más útil del trabajo:
entendí cuándo conviene que una regla la controle la base de datos y cuándo la aplicación, y qué se gana y
qué se pierde en cada caso.

Reforcé mucho las consultas SQL, sobre todo al ajustar los reportes para que solo consideraran partidos
jugados y al resolver reglas que dependen del tiempo, como las 48 horas para corregir un resultado o no
permitir cargar la planilla de un partido que todavía no se jugó. También entendí mejor cómo funciona un
programa completo, desde el formulario que completa el usuario hasta la consulta que llega a la base, y la
importancia de agrupar operaciones relacionadas en una transacción, como la tarjeta y su sanción, para que
los datos nunca queden a medias.

Por último, aprendí a dockerizar una aplicación y la importancia que tiene: cualquiera puede levantar el
proyecto con un solo comando, sin depender de cómo esté configurada su computadora, y es fácil volver a
crear la base desde cero para probar. Si lo hiciera de nuevo, definiría desde el principio en qué capa va
cada regla, para no tener que rehacer partes del trabajo.

**Joaquín Cáceres.** Me encargué principalmente del diseño del modelo relacional y de la creación de las
tablas, con sus claves, restricciones e índices únicos. Ese trabajo me hizo pensar con cuidado qué podía
garantizar la propia base de datos con `CHECK`, `UNIQUE` y claves foráneas, como las claves compuestas que
aseguran que solo convierten goles o reciben tarjetas los jugadores que figuran en la planilla, y qué reglas
necesitaban lógica adicional.

Reforcé los conceptos de normalización y de integridad referencial al llevar la letra a un esquema
concreto, y también las consultas SQL al trabajar sobre los casos borde del sistema. Participé en la
decisión de no usar triggers y en pasar esas reglas al backend, lo que me obligó a entender cómo se conecta
la aplicación con la base y cómo se validan los datos antes de guardarlos.

También valoré trabajar con Docker y con Git en equipo: tener la base y la aplicación en contenedores nos
permitió probar los cambios de cada uno en las mismas condiciones. Si lo hiciera de nuevo, dedicaría más
tiempo a definir al inicio qué reglas controla la base y cuáles la aplicación, para evitar idas y vueltas.

## 11. Bibliografía

- Oracle. *MySQL 8.0 Reference Manual* (CHECK constraints, GRANT, transacciones, CTE, funciones de ventana,
  WITH ROLLUP). <https://dev.mysql.com/doc/refman/8.0/en/>
- Pallets Projects. *Flask Documentation*. <https://flask.palletsprojects.com/>
- Oracle. *MySQL Connector/Python Developer Guide*. <https://dev.mysql.com/doc/connector-python/en/>
- Docker Inc. *Docker Compose documentation*. <https://docs.docker.com/compose/>
- Material teórico y prácticos del curso de Base de Datos 1, UCU (2026).
