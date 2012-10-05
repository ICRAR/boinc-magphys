DROP SCHEMA IF EXISTS magphys;
CREATE SCHEMA magphys;
USE magphys;

CREATE TABLE galaxy (
  galaxy_id        BIGINT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
  name             VARCHAR(128) NOT NULL,
  dimension_x      INTEGER UNSIGNED NOT NULL,
  dimension_y      INTEGER UNSIGNED NOT NULL,
  dimension_z      INTEGER UNSIGNED NOT NULL,
  redshift         FLOAT NOT NULL,
  sigma            FLOAT NOT NULL,
  create_time      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  image_time       TIMESTAMP,
  version_number   INTEGER UNSIGNED NOT NULL DEFAULT 1,
  current          BOOLEAN NOT NULL DEFAULT TRUE,
  galaxy_type      VARCHAR(10) character set utf8 collate utf8_bin NOT NULL,
  ra_cent          FLOAT,
  dec_cent         FLOAT,
  pixel_count      INTEGER,
  pixels_processed INTEGER
) CHARACTER SET utf8 ENGINE=InnoDB;

CREATE INDEX galaxy_name_ix ON galaxy(name, version_number);

CREATE TABLE fits_header (
  fitsheader_id BIGINT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
  galaxy_id     BIGINT UNSIGNED NOT NULL,
  keyword       VARCHAR(128) NOT NULL,
  value         VARCHAR(128) NOT NULL
) CHARACTER SET utf8 ENGINE=InnoDB;

CREATE INDEX fits_header_galaxy_ix ON fits_header(galaxy_id);

CREATE TABLE area (
  area_id      BIGINT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
  galaxy_id    BIGINT UNSIGNED NOT NULL,
  top_x        INTEGER UNSIGNED NOT NULL,
  top_y        INTEGER UNSIGNED NOT NULL,
  bottom_x     INTEGER UNSIGNED NOT NULL,
  bottom_y     INTEGER UNSIGNED NOT NULL,
  workunit_id  BIGINT UNSIGNED,
  update_time  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) CHARACTER SET utf8 ENGINE=InnoDB;

ALTER TABLE area ADD CONSTRAINT area_galaxy_fk FOREIGN KEY(galaxy_id) REFERENCES galaxy(galaxy_id);
CREATE INDEX area_galaxy_ix ON area(galaxy_id);
CREATE UNIQUE INDEX area_ix ON area(galaxy_id, top_x, top_y, bottom_x, bottom_y);

CREATE TABLE area_user (
  areauser_id  BIGINT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
  area_id      BIGINT UNSIGNED NOT NULL,
  userid       INTEGER NOT NULL,
  create_time  TIMESTAMP
) CHARACTER SET utf8 ENGINE=InnoDB;

ALTER TABLE area_user ADD CONSTRAINT areauser_area_fk FOREIGN KEY(area_id) REFERENCES area(area_id);
CREATE INDEX areauser_area_ix ON area_user(area_id);

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
  KEY (pxresult_id)
) CHARACTER SET utf8 ENGINE=InnoDB
PARTITION BY KEY (galaxy_id)
PARTITIONS 16;

CREATE INDEX pixel_result_area_ix ON pixel_result(area_id);
CREATE UNIQUE INDEX pixel_result_ix ON pixel_result(galaxy_id, x, y);

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

CREATE INDEX pxfilter_pxresult_ix ON pixel_filter(pxresult_id);

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

CREATE INDEX pxparameter_pxresult_ix ON pixel_parameter(pxresult_id);

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

CREATE INDEX pxhistogram_pxresult_ix ON pixel_histogram(pxresult_id);
CREATE INDEX pxhistogram_pxparameter_ix ON pixel_histogram(pxparameter_id);

CREATE TABLE user_pixel (
  userid BIGINT UNSIGNED NOT NULL PRIMARY KEY,
  pixel_count INTEGER
) CHARACTER SET utf8 ENGINE=InnoDB;

CREATE TABLE register (
  register_id   BIGINT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
  galaxy_name   VARCHAR(128) NOT NULL,
  redshift      FLOAT NOT NULL,
  galaxy_type   VARCHAR(10) character set utf8 collate utf8_bin NOT NULL,
  sigma         FLOAT NOT NULL,
  filename      VARCHAR(1000) NOT NULL,
  priority      INTEGER NOT NULL,
  register_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  create_time   TIMESTAMP NULL DEFAULT NULL
) CHARACTER SET utf8 ENGINE=InnoDB;

CREATE INDEX register_galaxy_name_ix ON register(galaxy_name);
CREATE INDEX register_time_ix ON register(create_time, register_time);

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

CREATE TABLE filter (
  filter_id     TINYINT UNSIGNED NOT NULL PRIMARY KEY,
  name          VARCHAR(30) NOT NULL,
  eff_lambda    DECIMAL(10, 4) NOT NULL,
  filter_number SMALLINT NOT NULL,
  sort_order    SMALLINT NOT NULL,
  ultraviolet   TINYINT(1) NOT NULL,
  optical       TINYINT(1) NOT NULL,
  infrared      TINYINT(1) NOT NULL,
  label         VARCHAR(20) NOT NULL
) CHARACTER SET utf8 ENGINE=InnoDB;

CREATE INDEX filter_filter_number_ix ON filter(filter_number);

INSERT INTO filter VALUES (0,  'GALEXFUV', 0.152,  123, 0,  1, 0, 0, 'FUV');
INSERT INTO filter VALUES (1,  'GALEXNUV', 0.231,  124, 1,  1, 0, 0, 'NUV');
INSERT INTO filter VALUES (2,  'SDSSu',    0.3534, 229, 2,  0, 1, 0, 'u');
INSERT INTO filter VALUES (3,  'SDSSg',    0.4742, 230, 3,  0, 1, 0, 'g');
INSERT INTO filter VALUES (4,  'PS1g',     0.481,  323, 4,  0, 1, 0, 'g');
INSERT INTO filter VALUES (5,  'PS1r',     0.617,  324, 5,  0, 1, 0, 'r');
INSERT INTO filter VALUES (6,  'SDSSr',    0.6189, 231, 6,  0, 1, 0, 'r');
INSERT INTO filter VALUES (7,  'PS1i',     0.752,  325, 7,  0, 1, 0, 'i');
INSERT INTO filter VALUES (8,  'SDSSi',    0.7595, 232, 8,  0, 1, 0, 'i');
INSERT INTO filter VALUES (9,  'PS1z',     0.866,  326, 9,  0, 1, 0, 'z');
INSERT INTO filter VALUES (10, 'SDSSz',    0.9032, 233, 10, 0, 1, 0, 'z');
INSERT INTO filter VALUES (11, 'PS1y',     0.962,  327, 11, 0, 1, 0, 'y');
INSERT INTO filter VALUES (12, 'WISEW1',   3.4,    280, 12, 0, 0, 1, '3.4');
INSERT INTO filter VALUES (13, 'IRAC3.6',  3.550,  153, 13, 0, 0, 1, '3.6');
INSERT INTO filter VALUES (14, 'IRAC4.5',  4.493,  154, 14, 0, 0, 1, '4.5');
INSERT INTO filter VALUES (15, 'WISEW2',   4.6,    281, 15, 0, 0, 1, '4.6');
INSERT INTO filter VALUES (16, 'IRAC5.8',  5.731,  155, 16, 0, 0, 1, '5.8');
INSERT INTO filter VALUES (17, 'IRAC8.0',  7.872,  156, 17, 0, 0, 1, '8.0');
INSERT INTO filter VALUES (18, 'WISEW3',   12.0,   282, 18, 0, 0, 1, '12');
INSERT INTO filter VALUES (19, 'WISEW4',   22.0,   283, 19, 0, 0, 1, '22');
INSERT INTO filter VALUES (20, 'MIPS24',   23.68,  157, 20, 0, 0, 1, '24');
INSERT INTO filter VALUES (21, 'MIPS70',   71.42,  158, 21, 0, 0, 1, '70');
INSERT INTO filter VALUES (22, 'PACS75',   75.0,   169, 22, 0, 0, 1, '75');
INSERT INTO filter VALUES (23, 'PACS110',  110.0,  170, 23, 0, 0, 1, '110');
INSERT INTO filter VALUES (24, 'MIPS160',  155.9,  159, 24, 0, 0, 1, '160');
INSERT INTO filter VALUES (25, 'PACS170',  170.0,  171, 25, 0, 0, 1, '170');
INSERT INTO filter VALUES (26, 'SPIRE250', 250.0,  172, 26, 0, 0, 1, '250');
INSERT INTO filter VALUES (27, 'SPIRE350', 350.0,  173, 27, 0, 0, 1, '350');
INSERT INTO filter VALUES (28, 'SPIRE500', 500.0,  174, 28, 0, 0, 1, '500');

CREATE TABLE image_filters_used (
  image_filters_used_id   BIGINT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR (1000) NOT NULL,
  filter_number_red SMALLINT,
  filter_number_green SMALLINT,
  filter_number_blue SMALLINT
) CHARACTER SET utf8 ENGINE=InnoDB;

CREATE INDEX image_filters_used_name_ix ON image_filters_used(name);
