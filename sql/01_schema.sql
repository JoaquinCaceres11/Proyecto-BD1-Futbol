DROP DATABASE IF EXISTS torneo_futbol5;
CREATE DATABASE torneo_futbol5 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE torneo_futbol5;


CREATE TABLE login (
    correo      VARCHAR(100) PRIMARY KEY,
    contrasenia VARCHAR(255) NOT NULL,
    rol         ENUM('administrador','planillero') NOT NULL,
    CONSTRAINT chk_login_correo CHECK (correo LIKE '%_@_%.__%')
);

CREATE TABLE facultad (
    id_facultad INT AUTO_INCREMENT PRIMARY KEY,
    nombre      VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE jugador (
    ci               VARCHAR(8)   PRIMARY KEY,
    nombre           VARCHAR(50)  NOT NULL,
    apellido         VARCHAR(50)  NOT NULL,
    email            VARCHAR(100) NOT NULL UNIQUE,
    fecha_nacimiento DATE         NOT NULL,
    id_facultad      INT          NOT NULL,
    tipo             ENUM('grado','posgrado','docente','funcionario') NOT NULL,
    FOREIGN KEY (id_facultad) REFERENCES facultad(id_facultad),
    CONSTRAINT chk_jugador_ci    CHECK (ci REGEXP '^[0-9]{7,8}$'),
    CONSTRAINT chk_jugador_email CHECK (email LIKE '%_@_%.__%')
);

CREATE TABLE torneo (
    id_torneo    INT AUTO_INCREMENT PRIMARY KEY,
    nombre       VARCHAR(100) NOT NULL,
    anio         INT          NOT NULL,
    semestre     TINYINT      NOT NULL,
    fecha_inicio DATE         NOT NULL,
    fecha_fin    DATE         NOT NULL,
    estado       ENUM('inscripcion','en curso','finalizado') NOT NULL DEFAULT 'inscripcion',
    UNIQUE (anio, semestre),
    CONSTRAINT chk_torneo_semestre CHECK (semestre IN (1,2)),
    CONSTRAINT chk_torneo_fechas   CHECK (fecha_fin >= fecha_inicio)
);

CREATE TABLE equipo (
    id_equipo   INT AUTO_INCREMENT PRIMARY KEY,
    nombre      VARCHAR(100) NOT NULL,
    id_torneo   INT NOT NULL,
    id_facultad INT NOT NULL,
    ci_capitan  VARCHAR(8) NULL,
    FOREIGN KEY (id_torneo)   REFERENCES torneo(id_torneo),
    FOREIGN KEY (id_facultad) REFERENCES facultad(id_facultad),
    FOREIGN KEY (ci_capitan)  REFERENCES jugador(ci),
    UNIQUE (id_torneo, nombre),
    UNIQUE (id_torneo, id_facultad)
);

CREATE TABLE equipo_jugador_torneo (
    id_equipo       INT         NOT NULL,
    ci_jugador      VARCHAR(8)  NOT NULL,
    id_torneo       INT         NOT NULL,
    numero_camiseta TINYINT     NOT NULL,
    PRIMARY KEY (id_equipo, ci_jugador, id_torneo),
    FOREIGN KEY (id_equipo)  REFERENCES equipo(id_equipo),
    FOREIGN KEY (ci_jugador) REFERENCES jugador(ci),
    FOREIGN KEY (id_torneo)  REFERENCES torneo(id_torneo),
    UNIQUE (ci_jugador, id_torneo),
    UNIQUE (id_equipo, numero_camiseta),
    CONSTRAINT chk_camiseta CHECK (numero_camiseta BETWEEN 1 AND 99)
);

CREATE TABLE complejo (
    id_complejo  INT AUTO_INCREMENT PRIMARY KEY,
    nombre       VARCHAR(100) NOT NULL UNIQUE,
    direccion    VARCHAR(150) NOT NULL,
    departamento VARCHAR(50)  NOT NULL
);

CREATE TABLE cancha (
    nombre_cancha VARCHAR(50) NOT NULL,
    id_complejo   INT         NOT NULL,
    superficie    ENUM('sintetico','parquet') NOT NULL,
    techada       BOOLEAN     NOT NULL DEFAULT FALSE,
    PRIMARY KEY (nombre_cancha, id_complejo),
    FOREIGN KEY (id_complejo) REFERENCES complejo(id_complejo)
);

CREATE TABLE turno (
    id_turno    INT AUTO_INCREMENT PRIMARY KEY,
    hora_inicio TIME NOT NULL,
    hora_fin    TIME NOT NULL,
    UNIQUE (hora_inicio),
    CONSTRAINT chk_turno CHECK (hora_fin > hora_inicio
                                AND hora_inicio >= '18:00:00'
                                AND hora_fin <= '23:00:00')
);

CREATE TABLE partido (
    id_partido          INT AUTO_INCREMENT PRIMARY KEY,
    id_torneo           INT NOT NULL,
    numero_fecha        INT NOT NULL,
    id_equipo_local     INT NOT NULL,
    id_equipo_visitante INT NOT NULL,
    dia                 DATE NOT NULL,
    id_turno            INT NOT NULL,
    nombre_cancha       VARCHAR(50) NOT NULL,
    id_complejo         INT NOT NULL,
    estado              ENUM('programado','jugado','postergado','cancelado') NOT NULL DEFAULT 'programado',
    fecha_jugado        DATETIME NULL,
    FOREIGN KEY (id_torneo)           REFERENCES torneo(id_torneo),
    FOREIGN KEY (id_equipo_local)     REFERENCES equipo(id_equipo),
    FOREIGN KEY (id_equipo_visitante) REFERENCES equipo(id_equipo),
    FOREIGN KEY (id_turno)            REFERENCES turno(id_turno),
    FOREIGN KEY (nombre_cancha, id_complejo) REFERENCES cancha(nombre_cancha, id_complejo),
    CONSTRAINT chk_distintos CHECK (id_equipo_local <> id_equipo_visitante),
    CONSTRAINT chk_fecha_pos CHECK (numero_fecha >= 1)
);

CREATE TABLE planilla_partido (
    id_partido INT        NOT NULL,
    ci_jugador VARCHAR(8) NOT NULL,
    id_equipo  INT        NOT NULL,
    PRIMARY KEY (id_partido, ci_jugador),
    FOREIGN KEY (id_partido) REFERENCES partido(id_partido),
    FOREIGN KEY (ci_jugador) REFERENCES jugador(ci),
    FOREIGN KEY (id_equipo)  REFERENCES equipo(id_equipo)
);

CREATE TABLE gol (
    id_gol     INT AUTO_INCREMENT PRIMARY KEY,
    id_partido INT        NOT NULL,
    ci_jugador VARCHAR(8) NOT NULL,
    minuto     TINYINT    NOT NULL,
    autogol    BOOLEAN    NOT NULL DEFAULT FALSE,
    FOREIGN KEY (id_partido, ci_jugador) REFERENCES planilla_partido(id_partido, ci_jugador),
    CONSTRAINT chk_gol_minuto CHECK (minuto BETWEEN 1 AND 60)
);

CREATE TABLE tarjeta (
    id_tarjeta INT AUTO_INCREMENT PRIMARY KEY,
    id_partido INT        NOT NULL,
    ci_jugador VARCHAR(8) NOT NULL,
    minuto     TINYINT    NOT NULL,
    color      ENUM('amarilla','roja') NOT NULL,
    FOREIGN KEY (id_partido, ci_jugador) REFERENCES planilla_partido(id_partido, ci_jugador),
    CONSTRAINT chk_tarjeta_minuto CHECK (minuto BETWEEN 1 AND 60)
);

CREATE TABLE sancion_jugador (
    id_sancion          INT AUTO_INCREMENT PRIMARY KEY,
    ci_jugador          VARCHAR(8) NOT NULL,
    id_torneo           INT        NOT NULL,
    motivo              ENUM('roja','acumulacion de amarillas','disciplinaria') NOT NULL,
    numero_fecha_inicio INT        NOT NULL,
    cantidad_fechas     INT        NOT NULL,
    FOREIGN KEY (ci_jugador) REFERENCES jugador(ci),
    FOREIGN KEY (id_torneo)  REFERENCES torneo(id_torneo),
    CONSTRAINT chk_sancion CHECK (cantidad_fechas >= 1 AND numero_fecha_inicio >= 1)
);


CREATE VIEW v_resultado_partido AS
SELECT p.id_partido, p.id_torneo, p.numero_fecha,
       p.id_equipo_local, p.id_equipo_visitante,
       (SELECT COUNT(*) FROM gol g JOIN planilla_partido pp
                ON pp.id_partido = g.id_partido AND pp.ci_jugador = g.ci_jugador
         WHERE g.id_partido = p.id_partido
           AND ((pp.id_equipo = p.id_equipo_local     AND g.autogol = FALSE)
             OR (pp.id_equipo = p.id_equipo_visitante AND g.autogol = TRUE))) AS goles_local,
       (SELECT COUNT(*) FROM gol g JOIN planilla_partido pp
                ON pp.id_partido = g.id_partido AND pp.ci_jugador = g.ci_jugador
         WHERE g.id_partido = p.id_partido
           AND ((pp.id_equipo = p.id_equipo_visitante AND g.autogol = FALSE)
             OR (pp.id_equipo = p.id_equipo_local     AND g.autogol = TRUE))) AS goles_visitante
FROM partido p
WHERE p.estado = 'jugado';

DROP USER IF EXISTS 'app_admin'@'%';
DROP USER IF EXISTS 'app_planillero'@'%';

CREATE USER 'app_admin'@'%'      IDENTIFIED BY 'admin_pass_2026';
CREATE USER 'app_planillero'@'%' IDENTIFIED BY 'planillero_pass_2026';


GRANT SELECT, INSERT, UPDATE, DELETE ON torneo_futbol5.* TO 'app_admin'@'%';

GRANT SELECT ON torneo_futbol5.facultad               TO 'app_planillero'@'%';
GRANT SELECT ON torneo_futbol5.jugador                TO 'app_planillero'@'%';
GRANT SELECT ON torneo_futbol5.torneo                 TO 'app_planillero'@'%';
GRANT SELECT ON torneo_futbol5.equipo                 TO 'app_planillero'@'%';
GRANT SELECT ON torneo_futbol5.equipo_jugador_torneo  TO 'app_planillero'@'%';
GRANT SELECT ON torneo_futbol5.complejo               TO 'app_planillero'@'%';
GRANT SELECT ON torneo_futbol5.cancha                 TO 'app_planillero'@'%';
GRANT SELECT ON torneo_futbol5.turno                  TO 'app_planillero'@'%';
GRANT SELECT ON torneo_futbol5.partido                TO 'app_planillero'@'%';
GRANT SELECT, INSERT, DELETE ON torneo_futbol5.sancion_jugador TO 'app_planillero'@'%';
GRANT SELECT ON torneo_futbol5.v_resultado_partido    TO 'app_planillero'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON torneo_futbol5.planilla_partido TO 'app_planillero'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON torneo_futbol5.gol              TO 'app_planillero'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON torneo_futbol5.tarjeta          TO 'app_planillero'@'%';
GRANT UPDATE (estado, fecha_jugado) ON torneo_futbol5.partido TO 'app_planillero'@'%';


FLUSH PRIVILEGES;
