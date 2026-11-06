USE torneo_futbol5;

INSERT INTO login (correo, contrasenia, rol) VALUES
('admin@ucu.edu.uy',      SHA2('admin123', 256),      'administrador'),
('planillero@ucu.edu.uy', SHA2('planillero123', 256), 'planillero');

INSERT INTO facultad (id_facultad, nombre) VALUES
(1, 'Ingenieria y Tecnologias'),
(2, 'Ciencias Empresariales'),
(3, 'Derecho'),
(4, 'Psicologia'),
(5, 'Ciencias de la Salud'),
(6, 'Humanidades y Comunicacion');

INSERT INTO turno (id_turno, hora_inicio, hora_fin) VALUES
(1,'18:00:00','19:00:00'),(2,'19:00:00','20:00:00'),(3,'20:00:00','21:00:00'),
(4,'21:00:00','22:00:00'),(5,'22:00:00','23:00:00');

INSERT INTO complejo (id_complejo, nombre, direccion, departamento) VALUES
(1,'Complejo Deportivo Pocitos','Av. Brasil 2850','Montevideo'),
(2,'Carrasco Sport Center','Av. Italia 6201','Montevideo');

INSERT INTO cancha (nombre_cancha, id_complejo, superficie, techada) VALUES
('Cancha 1',1,'sintetico',FALSE),
('Cancha 2',1,'sintetico',TRUE),
('Cancha A',2,'parquet',TRUE),
('Cancha B',2,'sintetico',FALSE);


INSERT INTO torneo (id_torneo, nombre, anio, semestre, fecha_inicio, fecha_fin, estado) VALUES
(1,'Torneo Interfacultades 2026-2',2026,2,'2026-09-28','2026-12-18','inscripcion');

INSERT INTO equipo (id_equipo, nombre, id_torneo, id_facultad, ci_capitan) VALUES
(1, 'Ingenieros FC', 1, 1, NULL),
(2, 'Los Contadores', 1, 2, NULL),
(3, 'Abogados United', 1, 3, NULL),
(4, 'Mente Sana', 1, 4, NULL),
(5, 'Salud Total', 1, 5, NULL),
(6, 'Letras y Goles', 1, 6, NULL);

INSERT INTO jugador (ci, nombre, apellido, email, fecha_nacimiento, id_facultad, tipo) VALUES
('4000101','Joaquin','Castro','joaquin.castro11@correo.ucu.edu.uy','2004-02-18',1,'grado'),
('4000102','Martin','Perez','martin.perez21@correo.ucu.edu.uy','2002-10-02',1,'grado'),
('4000103','Santiago','Olivera','santiago.olivera31@correo.ucu.edu.uy','2003-08-22',1,'grado'),
('4000104','Matias','Navarro','matias.navarro41@correo.ucu.edu.uy','2005-06-15',1,'grado'),
('4000105','Nicolas','Morales','nicolas.morales51@correo.ucu.edu.uy','2005-06-10',1,'grado'),
('4000106','Federico','Acosta','federico.acosta61@correo.ucu.edu.uy','1995-03-23',1,'posgrado'),
('4000107','Agustin','Diaz','agustin.diaz71@correo.ucu.edu.uy','2003-02-19',1,'grado'),
('4000201','Lucas','Suarez','lucas.suarez12@correo.ucu.edu.uy','2004-09-16',2,'grado'),
('4000202','Facundo','Alvarez','facundo.alvarez22@correo.ucu.edu.uy','2004-12-15',2,'grado'),
('4000203','Bruno','Delgado','bruno.delgado32@correo.ucu.edu.uy','2004-10-03',2,'grado'),
('4000204','Gonzalo','Gimenez','gonzalo.gimenez42@correo.ucu.edu.uy','2002-09-14',2,'grado'),
('4000205','Sebastian','Correa','sebastian.correa52@correo.ucu.edu.uy','2003-06-05',2,'grado'),
('4000206','Diego','Sosa','diego.sosa62@correo.ucu.edu.uy','1988-07-02',2,'docente'),
('4000207','Rodrigo','Gonzalez','rodrigo.gonzalez72@correo.ucu.edu.uy','1978-09-19',2,'funcionario'),
('4000301','Mateo','Cabrera','mateo.cabrera13@correo.ucu.edu.uy','2004-06-23',3,'grado'),
('4000302','Emiliano','Fagundez','emiliano.fagundez23@correo.ucu.edu.uy','2004-10-16',3,'grado'),
('4000303','Franco','Romero','franco.romero33@correo.ucu.edu.uy','2005-02-27',3,'grado'),
('4000304','Ignacio','Techera','ignacio.techera43@correo.ucu.edu.uy','2002-05-16',3,'grado'),
('4000305','Pablo','Lemos','pablo.lemos53@correo.ucu.edu.uy','2002-01-24',3,'grado'),
('4000306','Andres','Barreto','andres.barreto63@correo.ucu.edu.uy','1998-05-21',3,'posgrado'),
('4000307','Tomas','Rivero','tomas.rivero73@correo.ucu.edu.uy','2005-05-23',3,'grado'),
('4000401','Valentina','Viera','valentina.viera14@correo.ucu.edu.uy','2005-11-12',4,'grado'),
('4000402','Camila','Vazquez','camila.vazquez24@correo.ucu.edu.uy','2002-08-12',4,'grado'),
('4000403','Lucia','Pereira','lucia.pereira34@correo.ucu.edu.uy','2003-10-04',4,'grado'),
('4000404','Sofia','Nunez','sofia.nunez44@correo.ucu.edu.uy','2005-01-07',4,'grado'),
('4000405','Florencia','Lopez','florencia.lopez54@correo.ucu.edu.uy','2004-03-24',4,'grado'),
('4000406','Micaela','Cardozo','micaela.cardozo64@correo.ucu.edu.uy','1982-07-13',4,'docente'),
('4000407','Agustina','Benitez','agustina.benitez74@correo.ucu.edu.uy','2005-02-06',4,'grado'),
('4000501','Maria','Pintos','maria.pintos15@correo.ucu.edu.uy','2005-07-18',5,'grado'),
('4000502','Paula','Fernandez','paula.fernandez25@correo.ucu.edu.uy','2004-03-27',5,'grado'),
('4000503','Carolina','Rodriguez','carolina.rodriguez35@correo.ucu.edu.uy','2005-09-09',5,'grado'),
('4000504','Daniela','Ramos','daniela.ramos45@correo.ucu.edu.uy','2005-06-22',5,'grado'),
('4000505','Natalia','Amorin','natalia.amorin55@correo.ucu.edu.uy','2005-04-05',5,'grado'),
('4000506','Romina','Irigoyen','romina.irigoyen65@correo.ucu.edu.uy','1995-03-05',5,'posgrado'),
('4000507','Victoria','Machado','victoria.machado75@correo.ucu.edu.uy','1982-11-08',5,'funcionario'),
('4000601','Julieta','Silva','julieta.silva16@correo.ucu.edu.uy','2002-08-27',6,'grado'),
('4000602','Antonella','Bentancor','antonella.bentancor26@correo.ucu.edu.uy','2003-05-10',6,'grado'),
('4000603','Belen','Martinez','belen.martinez36@correo.ucu.edu.uy','2002-03-14',6,'grado'),
('4000604','Lorena','Garcia','lorena.garcia46@correo.ucu.edu.uy','2004-10-19',6,'grado'),
('4000605','Gabriela','Ferreira','gabriela.ferreira56@correo.ucu.edu.uy','2004-03-23',6,'grado'),
('4000606','Sabrina','Rodriguez','sabrina.rodriguez66@correo.ucu.edu.uy','1978-08-28',6,'docente'),
('4000607','Fernanda','Mendez','fernanda.mendez76@correo.ucu.edu.uy','2005-07-13',6,'grado');

INSERT INTO equipo_jugador_torneo (id_equipo, ci_jugador, id_torneo, numero_camiseta) VALUES
(1,'4000101',1,10),
(1,'4000102',1,7),
(1,'4000103',1,9),
(1,'4000104',1,5),
(1,'4000105',1,11),
(1,'4000106',1,8),
(1,'4000107',1,3),
(2,'4000201',1,10),
(2,'4000202',1,7),
(2,'4000203',1,9),
(2,'4000204',1,5),
(2,'4000205',1,11),
(2,'4000206',1,8),
(2,'4000207',1,3),
(3,'4000301',1,10),
(3,'4000302',1,7),
(3,'4000303',1,9),
(3,'4000304',1,5),
(3,'4000305',1,11),
(3,'4000306',1,8),
(3,'4000307',1,3),
(4,'4000401',1,10),
(4,'4000402',1,7),
(4,'4000403',1,9),
(4,'4000404',1,5),
(4,'4000405',1,11),
(4,'4000406',1,8),
(4,'4000407',1,3),
(5,'4000501',1,10),
(5,'4000502',1,7),
(5,'4000503',1,9),
(5,'4000504',1,5),
(5,'4000505',1,11),
(5,'4000506',1,8),
(5,'4000507',1,3),
(6,'4000601',1,10),
(6,'4000602',1,7),
(6,'4000603',1,9),
(6,'4000604',1,5),
(6,'4000605',1,11),
(6,'4000606',1,8),
(6,'4000607',1,3);

UPDATE equipo SET ci_capitan = '4000101' WHERE id_equipo = 1;
UPDATE equipo SET ci_capitan = '4000201' WHERE id_equipo = 2;
UPDATE equipo SET ci_capitan = '4000301' WHERE id_equipo = 3;
UPDATE equipo SET ci_capitan = '4000401' WHERE id_equipo = 4;
UPDATE equipo SET ci_capitan = '4000501' WHERE id_equipo = 5;
UPDATE equipo SET ci_capitan = '4000601' WHERE id_equipo = 6;

UPDATE torneo SET estado = 'en curso' WHERE id_torneo = 1;

INSERT INTO partido (id_partido,id_torneo,numero_fecha,id_equipo_local,id_equipo_visitante,dia,id_turno,nombre_cancha,id_complejo,estado,fecha_jugado) VALUES (1,1,1,1,6,'2026-10-05',1,'Cancha 1',1,'jugado','2026-10-05 19:30:00');
INSERT INTO planilla_partido (id_partido, ci_jugador, id_equipo) VALUES (1,'4000101',1),(1,'4000102',1),(1,'4000103',1),(1,'4000104',1),(1,'4000105',1),(1,'4000601',6),(1,'4000602',6),(1,'4000603',6),(1,'4000604',6),(1,'4000605',6);
INSERT INTO gol (id_partido, ci_jugador, minuto, autogol) VALUES (1,'4000101',8,0),(1,'4000102',22,0),(1,'4000101',40,0),(1,'4000602',33,0);
INSERT INTO tarjeta (id_partido, ci_jugador, minuto, color) VALUES (1,'4000604',20,'amarilla'),(1,'4000102',30,'amarilla');

INSERT INTO partido (id_partido,id_torneo,numero_fecha,id_equipo_local,id_equipo_visitante,dia,id_turno,nombre_cancha,id_complejo,estado,fecha_jugado) VALUES (2,1,1,2,5,'2026-10-05',2,'Cancha 1',1,'jugado','2026-10-05 20:30:00');
INSERT INTO planilla_partido (id_partido, ci_jugador, id_equipo) VALUES (2,'4000201',2),(2,'4000202',2),(2,'4000203',2),(2,'4000204',2),(2,'4000205',2),(2,'4000501',5),(2,'4000502',5),(2,'4000503',5),(2,'4000504',5),(2,'4000505',5);
INSERT INTO gol (id_partido, ci_jugador, minuto, autogol) VALUES (2,'4000201',12,0),(2,'4000204',50,0),(2,'4000501',20,0),(2,'4000502',55,0);
INSERT INTO tarjeta (id_partido, ci_jugador, minuto, color) VALUES (2,'4000503',45,'roja'),(2,'4000202',10,'amarilla');

INSERT INTO partido (id_partido,id_torneo,numero_fecha,id_equipo_local,id_equipo_visitante,dia,id_turno,nombre_cancha,id_complejo,estado,fecha_jugado) VALUES (3,1,1,3,4,'2026-10-05',1,'Cancha A',2,'jugado','2026-10-05 19:30:00');
INSERT INTO planilla_partido (id_partido, ci_jugador, id_equipo) VALUES (3,'4000301',3),(3,'4000302',3),(3,'4000303',3),(3,'4000304',3),(3,'4000305',3),(3,'4000401',4),(3,'4000402',4),(3,'4000403',4),(3,'4000404',4),(3,'4000405',4);
INSERT INTO gol (id_partido, ci_jugador, minuto, autogol) VALUES (3,'4000401',31,0);
INSERT INTO tarjeta (id_partido, ci_jugador, minuto, color) VALUES (3,'4000405',50,'amarilla');

INSERT INTO partido (id_partido,id_torneo,numero_fecha,id_equipo_local,id_equipo_visitante,dia,id_turno,nombre_cancha,id_complejo,estado,fecha_jugado) VALUES (4,1,2,1,5,'2026-10-12',1,'Cancha 1',1,'jugado','2026-10-12 19:30:00');
INSERT INTO planilla_partido (id_partido, ci_jugador, id_equipo) VALUES (4,'4000101',1),(4,'4000102',1),(4,'4000103',1),(4,'4000104',1),(4,'4000106',1),(4,'4000501',5),(4,'4000502',5),(4,'4000504',5),(4,'4000505',5),(4,'4000506',5);
INSERT INTO gol (id_partido, ci_jugador, minuto, autogol) VALUES (4,'4000103',27,0);
INSERT INTO tarjeta (id_partido, ci_jugador, minuto, color) VALUES (4,'4000102',15,'amarilla');

INSERT INTO partido (id_partido,id_torneo,numero_fecha,id_equipo_local,id_equipo_visitante,dia,id_turno,nombre_cancha,id_complejo,estado,fecha_jugado) VALUES (5,1,2,6,4,'2026-10-12',2,'Cancha A',2,'jugado','2026-10-12 20:30:00');
INSERT INTO planilla_partido (id_partido, ci_jugador, id_equipo) VALUES (5,'4000601',6),(5,'4000602',6),(5,'4000603',6),(5,'4000604',6),(5,'4000605',6),(5,'4000401',4),(5,'4000402',4),(5,'4000403',4),(5,'4000404',4),(5,'4000405',4);
INSERT INTO gol (id_partido, ci_jugador, minuto, autogol) VALUES (5,'4000602',15,0),(5,'4000603',41,1);
INSERT INTO tarjeta (id_partido, ci_jugador, minuto, color) VALUES (5,'4000604',55,'amarilla');

INSERT INTO partido (id_partido,id_torneo,numero_fecha,id_equipo_local,id_equipo_visitante,dia,id_turno,nombre_cancha,id_complejo,estado,fecha_jugado) VALUES (6,1,2,2,3,'2026-10-12',3,'Cancha 2',1,'jugado','2026-10-12 21:30:00');
INSERT INTO planilla_partido (id_partido, ci_jugador, id_equipo) VALUES (6,'4000201',2),(6,'4000202',2),(6,'4000203',2),(6,'4000204',2),(6,'4000206',2),(6,'4000301',3),(6,'4000302',3),(6,'4000303',3),(6,'4000304',3),(6,'4000305',3);
INSERT INTO gol (id_partido, ci_jugador, minuto, autogol) VALUES (6,'4000201',5,0),(6,'4000201',38,0);
INSERT INTO tarjeta (id_partido, ci_jugador, minuto, color) VALUES (6,'4000302',44,'amarilla');

INSERT INTO partido (id_partido,id_torneo,numero_fecha,id_equipo_local,id_equipo_visitante,dia,id_turno,nombre_cancha,id_complejo,estado,fecha_jugado) VALUES (7,1,3,1,4,'2026-10-19',2,'Cancha 1',1,'jugado','2026-10-19 20:30:00');
INSERT INTO planilla_partido (id_partido, ci_jugador, id_equipo) VALUES (7,'4000101',1),(7,'4000102',1),(7,'4000103',1),(7,'4000104',1),(7,'4000105',1),(7,'4000401',4),(7,'4000402',4),(7,'4000403',4),(7,'4000404',4),(7,'4000405',4);
INSERT INTO gol (id_partido, ci_jugador, minuto, autogol) VALUES (7,'4000101',10,0),(7,'4000103',58,0),(7,'4000401',14,0),(7,'4000402',30,0),(7,'4000401',44,0);
INSERT INTO tarjeta (id_partido, ci_jugador, minuto, color) VALUES (7,'4000102',52,'amarilla');

INSERT INTO partido (id_partido,id_torneo,numero_fecha,id_equipo_local,id_equipo_visitante,dia,id_turno,nombre_cancha,id_complejo,estado,fecha_jugado) VALUES (8,1,3,5,3,'2026-10-19',2,'Cancha B',2,'jugado','2026-10-19 20:30:00');
INSERT INTO planilla_partido (id_partido, ci_jugador, id_equipo) VALUES (8,'4000501',5),(8,'4000502',5),(8,'4000503',5),(8,'4000504',5),(8,'4000505',5),(8,'4000301',3),(8,'4000302',3),(8,'4000303',3),(8,'4000304',3),(8,'4000305',3);
INSERT INTO gol (id_partido, ci_jugador, minuto, autogol) VALUES (8,'4000501',6,0),(8,'4000501',19,0),(8,'4000502',33,0),(8,'4000504',47,0),(8,'4000301',52,0);
INSERT INTO tarjeta (id_partido, ci_jugador, minuto, color) VALUES (8,'4000301',53,'amarilla');

INSERT INTO partido (id_partido,id_torneo,numero_fecha,id_equipo_local,id_equipo_visitante,dia,id_turno,nombre_cancha,id_complejo,estado,fecha_jugado) VALUES (9,1,3,6,2,'2026-10-19',3,'Cancha A',2,'jugado','2026-10-19 21:30:00');
INSERT INTO planilla_partido (id_partido, ci_jugador, id_equipo) VALUES (9,'4000601',6),(9,'4000602',6),(9,'4000603',6),(9,'4000604',6),(9,'4000605',6),(9,'4000201',2),(9,'4000202',2),(9,'4000203',2),(9,'4000204',2),(9,'4000205',2);
INSERT INTO gol (id_partido, ci_jugador, minuto, autogol) VALUES (9,'4000202',21,0),(9,'4000201',36,0);
INSERT INTO tarjeta (id_partido, ci_jugador, minuto, color) VALUES (9,'4000604',48,'roja');

INSERT INTO partido (id_partido,id_torneo,numero_fecha,id_equipo_local,id_equipo_visitante,dia,id_turno,nombre_cancha,id_complejo,estado,fecha_jugado) VALUES (10,1,4,1,3,'2026-11-02',1,'Cancha 1',1,'programado',NULL);

INSERT INTO partido (id_partido,id_torneo,numero_fecha,id_equipo_local,id_equipo_visitante,dia,id_turno,nombre_cancha,id_complejo,estado,fecha_jugado) VALUES (11,1,4,4,2,'2026-11-02',2,'Cancha A',2,'postergado',NULL);

INSERT INTO partido (id_partido,id_torneo,numero_fecha,id_equipo_local,id_equipo_visitante,dia,id_turno,nombre_cancha,id_complejo,estado,fecha_jugado) VALUES (12,1,4,5,6,'2026-11-02',1,'Cancha B',2,'cancelado',NULL);

INSERT INTO sancion_jugador (ci_jugador, id_torneo, motivo, numero_fecha_inicio, cantidad_fechas) VALUES ('4000303', 1, 'disciplinaria', 4, 2);

INSERT INTO sancion_jugador (ci_jugador, id_torneo, motivo, numero_fecha_inicio, cantidad_fechas) VALUES
('4000503', 1, 'roja', 2, 1),
('4000604', 1, 'roja', 4, 1),
('4000102', 1, 'acumulacion de amarillas', 4, 1);