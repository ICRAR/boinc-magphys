DROP SCHEMA IF EXISTS magphys;
CREATE SCHEMA magphys;
USE magphys;

CREATE TABLE filter (
  filter_id     SMALLINT UNSIGNED NOT NULL PRIMARY KEY,
  name          VARCHAR(30) NOT NULL,
  eff_lambda    DECIMAL(10, 4) NOT NULL,
  filter_number SMALLINT NOT NULL,
  ultraviolet   TINYINT(1) NOT NULL,
  optical       TINYINT(1) NOT NULL,
  infrared      TINYINT(1) NOT NULL,
  label         VARCHAR(20) NOT NULL,

  INDEX (filter_number),
  INDEX (name)
) CHARACTER SET utf8 ENGINE=InnoDB;

INSERT INTO filter VALUES (0,  'GALEXFUV', 0.152,  123, 1, 0, 0, 'FUV');
INSERT INTO filter VALUES (1,  'GALEXNUV', 0.231,  124, 1, 0, 0, 'NUV');
INSERT INTO filter VALUES (2,  'SDSSu',    0.3534, 229, 0, 1, 0, 'u');
INSERT INTO filter VALUES (3,  'SDSSg',    0.4742, 230, 0, 1, 0, 'g');
INSERT INTO filter VALUES (4,  'PS1g',     0.481,  323, 0, 1, 0, 'g');
INSERT INTO filter VALUES (5,  'PS1r',     0.617,  324, 0, 1, 0, 'r');
INSERT INTO filter VALUES (6,  'SDSSr',    0.6189, 231, 0, 1, 0, 'r');
INSERT INTO filter VALUES (7,  'PS1i',     0.752,  325, 0, 1, 0, 'i');
INSERT INTO filter VALUES (8,  'SDSSi',    0.7595, 232, 0, 1, 0, 'i');
INSERT INTO filter VALUES (9,  'PS1z',     0.866,  326, 0, 1, 0, 'z');
INSERT INTO filter VALUES (10, 'SDSSz',    0.9032, 233, 0, 1, 0, 'z');
INSERT INTO filter VALUES (11, 'PS1y',     0.962,  327, 0, 1, 0, 'y');
INSERT INTO filter VALUES (12, 'WISEW1',   3.4,    280, 0, 0, 1, '3.4&#181;m');
INSERT INTO filter VALUES (13, 'IRAC3.6',  3.550,  153, 0, 0, 1, '3.6&#181;m');
INSERT INTO filter VALUES (14, 'IRAC4.5',  4.493,  154, 0, 0, 1, '4.5&#181;m');
INSERT INTO filter VALUES (15, 'WISEW2',   4.6,    281, 0, 0, 1, '4.6&#181;m');
INSERT INTO filter VALUES (16, 'IRAC5.8',  5.731,  155, 0, 0, 1, '5.8&#181;m');
INSERT INTO filter VALUES (17, 'IRAC8.0',  7.872,  156, 0, 0, 1, '8.0&#181;m');
INSERT INTO filter VALUES (18, 'WISEW3',   12.0,   282, 0, 0, 1, '12&#181;m');
INSERT INTO filter VALUES (19, 'WISEW4',   22.0,   283, 0, 0, 1, '22&#181;m');
INSERT INTO filter VALUES (20, 'MIPS24',   23.68,  157, 0, 0, 1, '24&#181;m');
INSERT INTO filter VALUES (21, 'MIPS70',   71.42,  158, 0, 0, 1, '70&#181;m');
INSERT INTO filter VALUES (22, 'PACS75',   75.0,   169, 0, 0, 1, '75&#181;m');
INSERT INTO filter VALUES (23, 'PACS110',  110.0,  170, 0, 0, 1, '110&#181;m');
INSERT INTO filter VALUES (24, 'MIPS160',  155.9,  159, 0, 0, 1, '160&#181;m');
INSERT INTO filter VALUES (25, 'PACS170',  170.0,  171, 0, 0, 1, '170&#181;m');
INSERT INTO filter VALUES (26, 'SPIRE250', 250.0,  172, 0, 0, 1, '250&#181;m');
INSERT INTO filter VALUES (27, 'SPIRE350', 350.0,  173, 0, 0, 1, '350&#181;m');
INSERT INTO filter VALUES (28, 'SPIRE500', 500.0,  174, 0, 0, 1, '500&#181;m');

CREATE TABLE galaxy_status (
  galaxy_status_id SMALLINT UNSIGNED NOT NULL PRIMARY KEY,
  description      VARCHAR(250) NOT NULL
) CHARACTER SET utf8 ENGINE=InnoDB;

INSERT INTO galaxy_status VALUES (0, 'COMPUTING');
INSERT INTO galaxy_status VALUES (1, 'PROCESSED');
INSERT INTO galaxy_status VALUES (2, 'ARCHIVED');
INSERT INTO galaxy_status VALUES (3, 'STORED');
INSERT INTO galaxy_status VALUES (4, 'DELETED');

CREATE TABLE run (
  run_id             BIGINT UNSIGNED NOT NULL PRIMARY KEY,
  short_description  VARCHAR(250) NOT NULL,
  long_description   VARCHAR(1000) NOT NULL,
  directory          VARCHAR(1000) NOT NULL,
  fpops_est          FLOAT NOT NULL,
  cobblestone_factor FLOAT NOT NULL,

  INDEX (short_description)
) CHARACTER SET utf8 ENGINE=InnoDB;

CREATE TABLE run_filter (
  run_filter_id BIGINT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
  run_id        BIGINT UNSIGNED NOT NULL,
  filter_id     SMALLINT UNSIGNED NOT NULL,

  FOREIGN KEY (run_id) REFERENCES run(run_id),
  FOREIGN KEY (filter_id) REFERENCES filter(filter_id),

  INDEX (run_id),
  INDEX (filter_id)
)  CHARACTER SET utf8 ENGINE=InnoDB;

CREATE TABLE run_file (
  run_file_id BIGINT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
  run_id      BIGINT UNSIGNED NOT NULL,
  redshift    DECIMAL(7, 5) NOT NULL,
  file_type   INTEGER NOT NULL,
  file_name   VARCHAR(1000) NOT NULL,
  size        BIGINT NOT NULL,
  md5_hash    VARCHAR (100) NOT NULL,

  FOREIGN KEY (run_id) REFERENCES run(run_id),

  INDEX (run_id)
) CHARACTER SET utf8 ENGINE=InnoDB;

CREATE TABLE register (
  register_id    BIGINT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
  galaxy_name    VARCHAR(128) NOT NULL,
  redshift       DECIMAL(7, 5) NOT NULL,
  galaxy_type    VARCHAR(10) character set utf8 collate utf8_bin NOT NULL,
  sigma          DECIMAL(3,2) NOT NULL,
  filename       VARCHAR(1000) NOT NULL,
  sigma_filename VARCHAR(1000) NULL,
  priority       INTEGER NOT NULL,
  register_time  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  create_time    TIMESTAMP NULL DEFAULT NULL,
  run_id         BIGINT UNSIGNED NOT NULL,

  INDEX (galaxy_name),
  INDEX (create_time, register_time),

  FOREIGN KEY(run_id) REFERENCES run(run_id)
) CHARACTER SET utf8 ENGINE=InnoDB;

CREATE TABLE galaxy (
  galaxy_id        BIGINT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
  run_id           BIGINT UNSIGNED NOT NULL,
  name             VARCHAR(128) NOT NULL,
  dimension_x      INTEGER UNSIGNED NOT NULL,
  dimension_y      INTEGER UNSIGNED NOT NULL,
  dimension_z      INTEGER UNSIGNED NOT NULL,
  redshift         DECIMAL(7, 5) NOT NULL,
  sigma            DECIMAL(3,2) NOT NULL,
  create_time      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  image_time       TIMESTAMP,
  version_number   INTEGER UNSIGNED NOT NULL DEFAULT 1,
  current          BOOLEAN NOT NULL DEFAULT TRUE,
  galaxy_type      VARCHAR(10) character set utf8 collate utf8_bin NOT NULL,
  ra_cent          FLOAT,
  dec_cent         FLOAT,
  pixel_count      INTEGER,
  pixels_processed INTEGER,
  status_id        SMALLINT UNSIGNED NOT NULL DEFAULT 0,

  FOREIGN KEY (run_id) REFERENCES run(run_id),
  FOREIGN KEY (status_id) REFERENCES galaxy_status(galaxy_status_id),

  INDEX (run_id),
  INDEX (name, version_number),
  INDEX (status_id)
) CHARACTER SET utf8 ENGINE=InnoDB;

CREATE TABLE fits_header (
  fitsheader_id BIGINT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
  galaxy_id     BIGINT UNSIGNED NOT NULL,
  keyword       VARCHAR(128) NOT NULL,
  value         VARCHAR(128) NOT NULL,

  FOREIGN KEY(galaxy_id) REFERENCES galaxy(galaxy_id),

  INDEX (galaxy_id)
) CHARACTER SET utf8 ENGINE=InnoDB;

CREATE TABLE area (
  area_id      BIGINT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
  galaxy_id    BIGINT UNSIGNED NOT NULL,
  top_x        INTEGER UNSIGNED NOT NULL,
  top_y        INTEGER UNSIGNED NOT NULL,
  bottom_x     INTEGER UNSIGNED NOT NULL,
  bottom_y     INTEGER UNSIGNED NOT NULL,
  workunit_id  BIGINT UNSIGNED,
  update_time  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY(galaxy_id) REFERENCES galaxy(galaxy_id),

  INDEX  (galaxy_id),
  UNIQUE (galaxy_id, top_x, top_y, bottom_x, bottom_y)
) CHARACTER SET utf8 ENGINE=InnoDB;

CREATE TABLE area_user (
  areauser_id  BIGINT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
  area_id      BIGINT UNSIGNED NOT NULL,
  userid       INTEGER NOT NULL,
  create_time  TIMESTAMP,

  FOREIGN KEY(area_id) REFERENCES area(area_id),

  INDEX (area_id)
) CHARACTER SET utf8 ENGINE=InnoDB;

CREATE TABLE pixel_result (
  pxresult_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  area_id     BIGINT UNSIGNED NOT NULL,
  galaxy_id   BIGINT UNSIGNED NOT NULL,
  x           INTEGER UNSIGNED NOT NULL,
  y           INTEGER UNSIGNED NOT NULL,
  workunit_id BIGINT UNSIGNED,
  i_sfh       DOUBLE,
  i_ir        DOUBLE,
  chi2        DOUBLE,
  redshift    DOUBLE,
  fmu_sfh     DOUBLE,
  fmu_ir      DOUBLE,
  mu          DOUBLE,
  tauv        DOUBLE,
  s_sfr       DOUBLE,
  m           DOUBLE,
  ldust       DOUBLE,
  t_w_bc      DOUBLE,
  t_c_ism     DOUBLE,
  xi_c_tot    DOUBLE,
  xi_pah_tot  DOUBLE,
  xi_mir_tot  DOUBLE,
  x_w_tot     DOUBLE,
  tvism       DOUBLE,
  mdust       DOUBLE,
  sfr         DOUBLE,
  i_opt       DOUBLE,
  dmstar      DOUBLE,
  dfmu_aux    DOUBLE,
  dz          DOUBLE,

  KEY    (pxresult_id),
  INDEX  (area_id),
  UNIQUE (galaxy_id, x, y)
) CHARACTER SET utf8 ENGINE=InnoDB
PARTITION BY KEY (galaxy_id)
PARTITIONS 16;


CREATE TABLE pixel_filter (
  pxfilter_id                BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  pxresult_id                BIGINT UNSIGNED NOT NULL,
  filter_name                VARCHAR(100) NOT NULL,
  observed_flux              DOUBLE NOT NULL,
  observational_uncertainty  DOUBLE NOT NULL,
  flux_bfm                   DOUBLE NOT NULL,
  KEY (pxfilter_id)
) CHARACTER SET utf8 ENGINE=InnoDB
PARTITION BY KEY (pxresult_id)
PARTITIONS 16;

CREATE INDEX pxresult_ix ON pixel_filter(pxresult_id);

CREATE TABLE pixel_parameter (
  pxparameter_id    BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  pxresult_id       BIGINT UNSIGNED NOT NULL,
  parameter_name_id TINYINT NOT NULL,
  percentile2_5     DOUBLE NOT NULL,
  percentile16      DOUBLE NOT NULL,
  percentile50      DOUBLE NOT NULL,
  percentile84      DOUBLE NOT NULL,
  percentile97_5    DOUBLE NOT NULL,
  high_prob_bin     DOUBLE NOT NULL,
  first_prob_bin    DOUBLE NOT NULL,
  last_prob_bin     DOUBLE NOT NULL,
  bin_step          DOUBLE NOT NULL,
  KEY (pxparameter_id)
) CHARACTER SET utf8 ENGINE=InnoDB
PARTITION BY KEY (pxresult_id)
PARTITIONS 16;

CREATE INDEX pxresult_ix ON pixel_parameter(pxresult_id);

CREATE TABLE pixel_histogram (
  pxhistogram_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  pxparameter_id BIGINT UNSIGNED NOT NULL,
  pxresult_id    BIGINT UNSIGNED NOT NULL,
  x_axis         DOUBLE NOT NULL,
  hist_value     DOUBLE NOT NULL,
  KEY (pxhistogram_id)
) CHARACTER SET utf8 ENGINE=InnoDB
PARTITION BY KEY (pxresult_id)
PARTITIONS 16;

CREATE INDEX pxresult_ix ON pixel_histogram(pxresult_id);
CREATE INDEX pxparameter_ix ON pixel_histogram(pxparameter_id);

CREATE TABLE user_pixel (
  userid BIGINT UNSIGNED NOT NULL PRIMARY KEY,
  pixel_count INTEGER
) CHARACTER SET utf8 ENGINE=InnoDB;

CREATE TABLE parameter_name (
  parameter_name_id TINYINT UNSIGNED NOT NULL PRIMARY KEY,
  name              VARCHAR(100) NOT NULL
) CHARACTER SET utf8 ENGINE=InnoDB;

INSERT INTO parameter_name VALUES (1, 'f_mu (SFH)');
INSERT INTO parameter_name VALUES (2, 'f_mu (IR)');
INSERT INTO parameter_name VALUES (3, 'mu parameter');
INSERT INTO parameter_name VALUES (4, 'tau_V');
INSERT INTO parameter_name VALUES (5, 'sSFR_0.1Gyr');
INSERT INTO parameter_name VALUES (6, 'M(stars)');
INSERT INTO parameter_name VALUES (7, 'Ldust');
INSERT INTO parameter_name VALUES (8, 'T_C^ISM');
INSERT INTO parameter_name VALUES (9, 'T_W^BC');
INSERT INTO parameter_name VALUES (10, 'xi_C^tot');
INSERT INTO parameter_name VALUES (11, 'xi_PAH^tot');
INSERT INTO parameter_name VALUES (12, 'xi_MIR^tot');
INSERT INTO parameter_name VALUES (13, 'xi_W^tot');
INSERT INTO parameter_name VALUES (14, 'tau_V^ISM');
INSERT INTO parameter_name VALUES (15, 'M(dust)');
INSERT INTO parameter_name VALUES (16, 'SFR_0.1Gyr');

CREATE TABLE image_filters_used (
  image_filters_used_id BIGINT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
  image_number          SMALLINT NOT NULL,
  galaxy_id             BIGINT UNSIGNED NOT NULL,
  filter_id_red         SMALLINT UNSIGNED NOT NULL,
  filter_id_green       SMALLINT UNSIGNED NOT NULL,
  filter_id_blue        SMALLINT UNSIGNED NOT NULL,

  FOREIGN KEY (galaxy_id) REFERENCES galaxy(galaxy_id),
  FOREIGN KEY (filter_id_red) REFERENCES filter(filter_id),
  FOREIGN KEY (filter_id_green) REFERENCES filter(filter_id),
  FOREIGN KEY (filter_id_blue) REFERENCES filter(filter_id),

  INDEX (galaxy_id, image_number)
) CHARACTER SET utf8 ENGINE=InnoDB;

CREATE TABLE docmosis_task (
  task_id       BIGINT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
  userid        INTEGER NOT NULL,
  worker_token  VARCHAR(32) NULL DEFAULT NULL,
  create_time   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  finish_time   TIMESTAMP NULL DEFAULT NULL,
  status        SMALLINT UNSIGNED NOT NULL DEFAULT '0'

) ENGINE=InnoDB DEFAULT CHARSET=utf8;


CREATE TABLE docmosis_task_galaxy (
  task_id       BIGINT UNSIGNED NOT NULL,
  galaxy_id     BIGINT UNSIGNED NOT NULL,

  PRIMARY KEY (task_id,galaxy_id),
  KEY task_id (task_id),
  KEY galaxy_id (galaxy_id),

  FOREIGN KEY (task_id) REFERENCES docmosis_task(task_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
