USE torneo_futbol5;

-- R1. Tabla de posiciones
WITH r AS (
    SELECT id_equipo_local AS id_equipo, goles_local AS gf, goles_visitante AS gc
      FROM v_resultado_partido WHERE id_torneo = 1
    UNION ALL
    SELECT id_equipo_visitante, goles_visitante, goles_local
      FROM v_resultado_partido WHERE id_torneo = 1
)
SELECT e.nombre AS equipo,
       COUNT(r.id_equipo)                                        AS pj,
       COALESCE(SUM(r.gf > r.gc), 0)                             AS pg,
       COALESCE(SUM(r.gf = r.gc), 0)                             AS pe,
       COALESCE(SUM(r.gf < r.gc), 0)                             AS pp,
       COALESCE(SUM(r.gf), 0)                                    AS gf,
       COALESCE(SUM(r.gc), 0)                                    AS gc,
       COALESCE(SUM(r.gf) - SUM(r.gc), 0)                        AS dif,
       COALESCE(SUM(CASE WHEN r.gf > r.gc THEN 3
                         WHEN r.gf = r.gc THEN 1 ELSE 0 END), 0) AS puntos
  FROM equipo e
  LEFT JOIN r ON r.id_equipo = e.id_equipo
 WHERE e.id_torneo = 1
 GROUP BY e.id_equipo, e.nombre
 ORDER BY puntos DESC, dif DESC, gf DESC;

-- R2. Tabla de goleadores
SELECT j.ci, j.nombre, j.apellido, e.nombre AS equipo, COUNT(*) AS goles
  FROM gol g
  JOIN partido p ON p.id_partido = g.id_partido
  JOIN jugador j ON j.ci = g.ci_jugador
  JOIN equipo_jugador_torneo ejt ON ejt.ci_jugador = j.ci AND ejt.id_torneo = p.id_torneo
  JOIN equipo e ON e.id_equipo = ejt.id_equipo
 WHERE p.id_torneo = 1 AND g.autogol = FALSE
 GROUP BY j.ci, j.nombre, j.apellido, e.nombre
 ORDER BY goles DESC, j.apellido
 LIMIT 10;

-- R3. Fair play por equipo
SELECT e.nombre AS equipo,
       COALESCE(SUM(t.color = 'amarilla'), 0) AS amarillas,
       COALESCE(SUM(t.color = 'roja'), 0)     AS rojas,
       COALESCE(SUM(CASE t.color WHEN 'amarilla' THEN 1 WHEN 'roja' THEN 3 ELSE 0 END), 0) AS puntos_fair_play
  FROM equipo e
  LEFT JOIN planilla_partido pp ON pp.id_equipo = e.id_equipo
  LEFT JOIN tarjeta t ON t.id_partido = pp.id_partido AND t.ci_jugador = pp.ci_jugador
 WHERE e.id_torneo = 1
 GROUP BY e.id_equipo, e.nombre
 ORDER BY puntos_fair_play ASC;


-- R4. Promedio de goles por fecha y edicion
SELECT IF(GROUPING(numero_fecha) = 1, 'Toda la edicion', CAST(numero_fecha AS CHAR)) AS fecha,
       COUNT(*)                                          AS partidos,
       SUM(goles_local + goles_visitante)                AS goles,
       ROUND(AVG(goles_local + goles_visitante), 2)      AS promedio_goles
  FROM v_resultado_partido
 WHERE id_torneo = 1
 GROUP BY numero_fecha WITH ROLLUP;


-- R5. Canchas y turnos mas utilizados
SELECT c.nombre AS complejo, p.nombre_cancha, t.hora_inicio, t.hora_fin, COUNT(*) AS veces_usada
  FROM partido p
  JOIN complejo c ON c.id_complejo = p.id_complejo
  JOIN turno t    ON t.id_turno = p.id_turno
 WHERE p.id_torneo = 1 AND p.estado = 'jugado'
 GROUP BY c.nombre, p.nombre_cancha, t.id_turno, t.hora_inicio, t.hora_fin
 ORDER BY veces_usada DESC, c.nombre, p.nombre_cancha;

-- ---------------------------------------------------------------
-- R6. Cantidad de jugadores por facultad y por tipo
-- ---------------------------------------------------------------
SELECT f.nombre AS facultad, j.tipo, COUNT(*) AS cantidad
  FROM jugador j
  JOIN facultad f ON f.id_facultad = j.id_facultad
 GROUP BY f.nombre, j.tipo
 ORDER BY f.nombre, j.tipo;

-- R7. Inscriptos que nunca figuraron en planilla
SELECT j.ci, j.nombre, j.apellido, e.nombre AS equipo
  FROM equipo_jugador_torneo ejt
  JOIN jugador j ON j.ci = ejt.ci_jugador
  JOIN equipo e  ON e.id_equipo = ejt.id_equipo
  LEFT JOIN planilla_partido pp ON pp.ci_jugador = ejt.ci_jugador
 WHERE ejt.id_torneo = 1 AND pp.ci_jugador IS NULL
 ORDER BY e.nombre, j.apellido;

-- R8. Sanciones por equipo y motivo
SELECT e.nombre AS equipo, s.motivo, COUNT(*) AS cantidad
  FROM sancion_jugador s
  JOIN equipo_jugador_torneo ejt ON ejt.ci_jugador = s.ci_jugador AND ejt.id_torneo = s.id_torneo
  JOIN equipo e ON e.id_equipo = ejt.id_equipo
 WHERE s.id_torneo = 1
 GROUP BY e.nombre, s.motivo
 ORDER BY e.nombre, s.motivo;

-- R9. Porcentaje de partidos por estado
SELECT estado, COUNT(*) AS cantidad,
       ROUND(100 * COUNT(*) / (SELECT COUNT(*) FROM partido WHERE id_torneo = 1), 2) AS porcentaje
  FROM partido
 WHERE id_torneo = 1
 GROUP BY estado;

-- R10. Jugadores en riesgo de suspension
SELECT j.ci, j.nombre, j.apellido, e.nombre AS equipo, COUNT(*) AS amarillas
  FROM tarjeta t
  JOIN partido p ON p.id_partido = t.id_partido
  JOIN jugador j ON j.ci = t.ci_jugador
  JOIN equipo_jugador_torneo ejt ON ejt.ci_jugador = j.ci AND ejt.id_torneo = p.id_torneo
  JOIN equipo e ON e.id_equipo = ejt.id_equipo
 WHERE p.id_torneo = 1 AND t.color = 'amarilla'
 GROUP BY j.ci, j.nombre, j.apellido, e.nombre
HAVING COUNT(*) = 2;

-- R11. Jugadores suspendidos en una fecha
SELECT j.ci, j.nombre, j.apellido, e.nombre AS equipo, s.motivo,
       s.numero_fecha_inicio, s.cantidad_fechas
  FROM sancion_jugador s
  JOIN jugador j ON j.ci = s.ci_jugador
  JOIN equipo_jugador_torneo ejt ON ejt.ci_jugador = s.ci_jugador AND ejt.id_torneo = s.id_torneo
  JOIN equipo e ON e.id_equipo = ejt.id_equipo
 WHERE s.id_torneo = 1
   AND 4 >= s.numero_fecha_inicio
   AND 4 <  s.numero_fecha_inicio + s.cantidad_fechas
 ORDER BY e.nombre;

-- R12. Partidos con mas goles (Ranking con Window Function DENSE_RANK)
WITH partidos_goles AS (
    SELECT r.numero_fecha, el.nombre AS local, r.goles_local, r.goles_visitante, ev.nombre AS visitante,
           (r.goles_local + r.goles_visitante) AS total_goles
      FROM v_resultado_partido r
      JOIN equipo el ON el.id_equipo = r.id_equipo_local
      JOIN equipo ev ON ev.id_equipo = r.id_equipo_visitante
     WHERE r.id_torneo = 1
)
SELECT DENSE_RANK() OVER (ORDER BY total_goles DESC) AS puesto,
       numero_fecha, local, goles_local, goles_visitante, visitante, total_goles
  FROM partidos_goles
 ORDER BY puesto, numero_fecha
 LIMIT 5;
