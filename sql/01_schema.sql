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


DELIMITER $$

CREATE TRIGGER trg_equipo_capitan
BEFORE UPDATE ON equipo
FOR EACH ROW
BEGIN
    DECLARE v_cant INT;
    IF NEW.ci_capitan IS NOT NULL THEN
        SELECT COUNT(*) INTO v_cant FROM equipo_jugador_torneo
         WHERE id_equipo = NEW.id_equipo AND ci_jugador = NEW.ci_capitan;
        IF v_cant = 0 THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El capitan debe ser jugador del plantel del equipo';
        END IF;
    END IF;
END$$

CREATE TRIGGER trg_plantel_insert
BEFORE INSERT ON equipo_jugador_torneo
FOR EACH ROW
BEGIN
    DECLARE v_estado VARCHAR(20);
    DECLARE v_fac_equipo INT;
    DECLARE v_fac_jugador INT;
    DECLARE v_tipo VARCHAR(20);
    DECLARE v_cant INT;
    DECLARE v_cant_staff INT;
    DECLARE v_torneo_equipo INT;

    SELECT estado INTO v_estado FROM torneo WHERE id_torneo = NEW.id_torneo;
    IF v_estado <> 'inscripcion' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El plantel solo puede modificarse en etapa de inscripcion';
    END IF;

    SELECT id_facultad, id_torneo INTO v_fac_equipo, v_torneo_equipo
      FROM equipo WHERE id_equipo = NEW.id_equipo;
    IF v_torneo_equipo <> NEW.id_torneo THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El equipo no pertenece al torneo indicado';
    END IF;

    SELECT id_facultad, tipo INTO v_fac_jugador, v_tipo FROM jugador WHERE ci = NEW.ci_jugador;
    IF v_fac_jugador <> v_fac_equipo THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El jugador no pertenece a la facultad del equipo';
    END IF;

    SELECT COUNT(*) INTO v_cant FROM equipo_jugador_torneo WHERE id_equipo = NEW.id_equipo;
    IF v_cant >= 10 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El plantel ya tiene 10 jugadores';
    END IF;

    IF v_tipo IN ('docente','funcionario') THEN
        SELECT COUNT(*) INTO v_cant_staff
          FROM equipo_jugador_torneo ejt JOIN jugador j ON j.ci = ejt.ci_jugador
         WHERE ejt.id_equipo = NEW.id_equipo AND j.tipo IN ('docente','funcionario');
        IF v_cant_staff >= 2 THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El plantel admite maximo 2 docentes/funcionarios';
        END IF;
    END IF;
END$$

CREATE TRIGGER trg_plantel_delete
BEFORE DELETE ON equipo_jugador_torneo
FOR EACH ROW
BEGIN
    DECLARE v_estado VARCHAR(20);
    SELECT estado INTO v_estado FROM torneo WHERE id_torneo = OLD.id_torneo;
    IF v_estado <> 'inscripcion' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El plantel solo puede modificarse en etapa de inscripcion';
    END IF;
END$$

CREATE TRIGGER trg_partido_insert
BEFORE INSERT ON partido
FOR EACH ROW
BEGIN
    DECLARE v_cant INT;
    DECLARE v_t1 INT;
    DECLARE v_t2 INT;

    SELECT id_torneo INTO v_t1 FROM equipo WHERE id_equipo = NEW.id_equipo_local;
    SELECT id_torneo INTO v_t2 FROM equipo WHERE id_equipo = NEW.id_equipo_visitante;
    IF v_t1 <> NEW.id_torneo OR v_t2 <> NEW.id_torneo THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Ambos equipos deben pertenecer al torneo del partido';
    END IF;

    SELECT COUNT(*) INTO v_cant FROM equipo_jugador_torneo WHERE id_equipo = NEW.id_equipo_local;
    IF v_cant < 5 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El equipo local tiene menos de 5 jugadores';
    END IF;
    SELECT COUNT(*) INTO v_cant FROM equipo_jugador_torneo WHERE id_equipo = NEW.id_equipo_visitante;
    IF v_cant < 5 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El equipo visitante tiene menos de 5 jugadores';
    END IF;

    SELECT COUNT(*) INTO v_cant FROM partido
     WHERE id_torneo = NEW.id_torneo AND estado <> 'cancelado'
       AND ((id_equipo_local = NEW.id_equipo_local AND id_equipo_visitante = NEW.id_equipo_visitante)
         OR (id_equipo_local = NEW.id_equipo_visitante AND id_equipo_visitante = NEW.id_equipo_local));
    IF v_cant > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Estos equipos ya tienen un partido en la edicion';
    END IF;

    SELECT COUNT(*) INTO v_cant FROM partido
     WHERE id_torneo = NEW.id_torneo AND numero_fecha = NEW.numero_fecha AND estado <> 'cancelado'
       AND (id_equipo_local IN (NEW.id_equipo_local, NEW.id_equipo_visitante)
         OR id_equipo_visitante IN (NEW.id_equipo_local, NEW.id_equipo_visitante));
    IF v_cant > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Un equipo ya tiene partido en esa fecha del torneo';
    END IF;

    SELECT COUNT(*) INTO v_cant FROM partido
     WHERE dia = NEW.dia AND id_turno = NEW.id_turno
       AND nombre_cancha = NEW.nombre_cancha AND id_complejo = NEW.id_complejo
       AND estado <> 'cancelado';
    IF v_cant > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'La cancha ya tiene un partido en ese dia y turno';
    END IF;
END$$

CREATE TRIGGER trg_partido_delete
BEFORE DELETE ON partido
FOR EACH ROW
BEGIN
    IF OLD.estado = 'jugado' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Un partido jugado no puede eliminarse';
    END IF;
END$$

CREATE TRIGGER trg_partido_update
BEFORE UPDATE ON partido
FOR EACH ROW
BEGIN
    DECLARE v_fin TIME;
    DECLARE v_cant INT;
    DECLARE v_cant_visit INT;

    IF NEW.id_torneo <> OLD.id_torneo
       OR NEW.id_equipo_local <> OLD.id_equipo_local
       OR NEW.id_equipo_visitante <> OLD.id_equipo_visitante THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'No se pueden cambiar los equipos ni el torneo de un partido';
    END IF;

    IF OLD.estado IN ('jugado','cancelado') AND NEW.estado <> OLD.estado THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Un partido jugado o cancelado no puede cambiar de estado';
    END IF;

    IF NEW.numero_fecha <> OLD.numero_fecha OR NEW.dia <> OLD.dia OR NEW.id_turno <> OLD.id_turno
       OR NEW.nombre_cancha <> OLD.nombre_cancha OR NEW.id_complejo <> OLD.id_complejo THEN

        IF OLD.estado IN ('jugado','cancelado') THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Un partido jugado o cancelado no puede reprogramarse';
        END IF;

        SELECT COUNT(*) INTO v_cant FROM partido
         WHERE id_torneo = NEW.id_torneo AND numero_fecha = NEW.numero_fecha
           AND estado <> 'cancelado' AND id_partido <> NEW.id_partido
           AND (id_equipo_local IN (NEW.id_equipo_local, NEW.id_equipo_visitante)
             OR id_equipo_visitante IN (NEW.id_equipo_local, NEW.id_equipo_visitante));
        IF v_cant > 0 THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Un equipo ya tiene partido en esa fecha del torneo';
        END IF;

        SELECT COUNT(*) INTO v_cant FROM partido
         WHERE dia = NEW.dia AND id_turno = NEW.id_turno
           AND nombre_cancha = NEW.nombre_cancha AND id_complejo = NEW.id_complejo
           AND estado <> 'cancelado' AND id_partido <> NEW.id_partido;
        IF v_cant > 0 THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'La cancha ya tiene un partido en ese dia y turno';
        END IF;
    END IF;

    IF NEW.estado = 'jugado' AND OLD.estado <> 'jugado' THEN
        IF OLD.estado = 'postergado' THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Un partido postergado debe reprogramarse antes de marcarse jugado';
        END IF;

        SELECT hora_fin INTO v_fin FROM turno WHERE id_turno = NEW.id_turno;
        IF TIMESTAMP(NEW.dia, v_fin) > NOW() THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El dia y turno del partido todavia no pasaron';
        END IF;

        SELECT COUNT(*) INTO v_cant FROM planilla_partido
         WHERE id_partido = NEW.id_partido AND id_equipo = NEW.id_equipo_local;
        SELECT COUNT(*) INTO v_cant_visit FROM planilla_partido
         WHERE id_partido = NEW.id_partido AND id_equipo = NEW.id_equipo_visitante;
        IF v_cant = 0 OR v_cant_visit = 0 THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Carga la planilla de ambos equipos antes de marcar jugado';
        END IF;

        SET NEW.fecha_jugado = NOW();
    END IF;
END$$


CREATE TRIGGER trg_planilla_insert
BEFORE INSERT ON planilla_partido
FOR EACH ROW
BEGIN
    DECLARE v_cant INT;
    DECLARE v_fecha INT;
    DECLARE v_torneo INT;
    DECLARE v_local INT;
    DECLARE v_visit INT;

    SELECT id_torneo, numero_fecha, id_equipo_local, id_equipo_visitante
      INTO v_torneo, v_fecha, v_local, v_visit
      FROM partido WHERE id_partido = NEW.id_partido;

    IF NEW.id_equipo NOT IN (v_local, v_visit) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El equipo no participa en el partido';
    END IF;

    SELECT COUNT(*) INTO v_cant FROM equipo_jugador_torneo
     WHERE id_equipo = NEW.id_equipo AND ci_jugador = NEW.ci_jugador AND id_torneo = v_torneo;
    IF v_cant = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El jugador no integra el plantel del equipo';
    END IF;

    SELECT COUNT(*) INTO v_cant FROM sancion_jugador
     WHERE ci_jugador = NEW.ci_jugador AND id_torneo = v_torneo
       AND v_fecha >= numero_fecha_inicio
       AND v_fecha <  numero_fecha_inicio + cantidad_fechas;
    IF v_cant > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El jugador esta suspendido para esta fecha';
    END IF;
END$$


CREATE TRIGGER trg_tarjeta_sancion
AFTER INSERT ON tarjeta
FOR EACH ROW
BEGIN
    DECLARE v_torneo INT;
    DECLARE v_fecha INT;
    DECLARE v_amarillas INT;

    SELECT id_torneo, numero_fecha INTO v_torneo, v_fecha
      FROM partido WHERE id_partido = NEW.id_partido;

    IF NEW.color = 'roja' THEN
        INSERT INTO sancion_jugador (ci_jugador, id_torneo, motivo, numero_fecha_inicio, cantidad_fechas)
        VALUES (NEW.ci_jugador, v_torneo, 'roja', v_fecha + 1, 1);
    ELSE
        SELECT COUNT(*) INTO v_amarillas
          FROM tarjeta t JOIN partido p ON p.id_partido = t.id_partido
         WHERE t.ci_jugador = NEW.ci_jugador AND p.id_torneo = v_torneo AND t.color = 'amarilla';
        IF v_amarillas = 3 THEN
            INSERT INTO sancion_jugador (ci_jugador, id_torneo, motivo, numero_fecha_inicio, cantidad_fechas)
            VALUES (NEW.ci_jugador, v_torneo, 'acumulacion de amarillas', v_fecha + 1, 1);
        END IF;
    END IF;
END$$

CREATE TRIGGER trg_tarjeta_borrar_sancion
AFTER DELETE ON tarjeta
FOR EACH ROW
BEGIN
    DECLARE v_torneo INT;
    DECLARE v_fecha INT;
    DECLARE v_amarillas INT;

    SELECT id_torneo, numero_fecha INTO v_torneo, v_fecha
      FROM partido WHERE id_partido = OLD.id_partido;

    IF OLD.color = 'roja' THEN
        DELETE FROM sancion_jugador
         WHERE ci_jugador = OLD.ci_jugador AND id_torneo = v_torneo
           AND motivo = 'roja' AND numero_fecha_inicio = v_fecha + 1
         LIMIT 1;
    ELSE
        SELECT COUNT(*) INTO v_amarillas
          FROM tarjeta t JOIN partido p ON p.id_partido = t.id_partido
         WHERE t.ci_jugador = OLD.ci_jugador AND p.id_torneo = v_torneo AND t.color = 'amarilla';
        IF v_amarillas < 3 THEN
            DELETE FROM sancion_jugador
             WHERE ci_jugador = OLD.ci_jugador AND id_torneo = v_torneo
               AND motivo = 'acumulacion de amarillas';
        END IF;
    END IF;
END$$

DELIMITER ;


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
GRANT SELECT ON torneo_futbol5.sancion_jugador        TO 'app_planillero'@'%';
GRANT SELECT ON torneo_futbol5.v_resultado_partido    TO 'app_planillero'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON torneo_futbol5.planilla_partido TO 'app_planillero'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON torneo_futbol5.gol              TO 'app_planillero'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON torneo_futbol5.tarjeta          TO 'app_planillero'@'%';
GRANT UPDATE (estado, fecha_jugado) ON torneo_futbol5.partido TO 'app_planillero'@'%';


FLUSH PRIVILEGES;
