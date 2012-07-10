DROP SCHEMA IF EXISTS magphys;
CREATE SCHEMA magphys;
USE magphys;

CREATE TABLE galaxy (
  galaxy_id   BIGINT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
  name        VARCHAR(128) NOT NULL,
  dimension_x INTEGER UNSIGNED NOT NULL,
  dimension_y INTEGER UNSIGNED NOT NULL,
  dimension_z INTEGER UNSIGNED NOT NULL,
  redshift    FLOAT NOT NULL
) CHARACTER SET utf8 ENGINE=InnoDB;

CREATE UNIQUE INDEX galaxy_name_ix ON galaxy(name);

CREATE TABLE square (
  square_id    BIGINT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
  galaxy_id    BIGINT UNSIGNED NOT NULL,
  top_x        INTEGER UNSIGNED NOT NULL,
  top_y        INTEGER UNSIGNED NOT NULL,
  size         INTEGER UNSIGNED NOT NULL,
  wu_generated DATETIME DEFAULT NULL
) CHARACTER SET utf8 ENGINE=InnoDB;

ALTER TABLE square ADD CONSTRAINT square_galaxy_fk FOREIGN KEY(galaxy_id) REFERENCES galaxy(galaxy_id);
CREATE INDEX square_galaxy_ix ON square(galaxy_id);
CREATE UNIQUE INDEX square_ix ON square(galaxy_id, top_x, top_y, size);
CREATE INDEX wu_generation_id ON square(wu_generated);

CREATE TABLE pixel_result (
  pxresult_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  square_id   BIGINT UNSIGNED NOT NULL,
  galaxy_id   BIGINT UNSIGNED NOT NULL,
  x           INTEGER UNSIGNED NOT NULL,
  y           INTEGER UNSIGNED NOT NULL,
  workunit_id INTEGER,
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

CREATE INDEX pixel_result_square_ix ON pixel_result(square_id);
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

CREATE TABLE pixel_parameter (
  pxparameter_id     BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  pxresult_id        BIGINT UNSIGNED NOT NULL,
  parameter_name     VARCHAR(100) NOT NULL,
  percentile2_5      DOUBLE NOT NULL,
  percentile16       DOUBLE NOT NULL,
  percentile50       DOUBLE NOT NULL,
  percentile84       DOUBLE NOT NULL,
  percentile97_5     DOUBLE NOT NULL,
  KEY (pxparameter_id)
) CHARACTER SET utf8 ENGINE=InnoDB
PARTITION BY KEY (pxresult_id)
PARTITIONS 16;


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

CREATE TABLE pixel_user (
  pxuser_id                  BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  pxresult_id                BIGINT UNSIGNED NOT NULL,
  userid                     INTEGER NOT NULL,
  create_time                TIMESTAMP,
  KEY (pxuser_id)
) CHARACTER SET utf8 ENGINE=InnoDB
PARTITION BY KEY (pxresult_id)
PARTITIONS 16;